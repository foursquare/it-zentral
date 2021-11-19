from datetime import datetime
import json
import logging
import random
import time
import uuid
from urllib.parse import urlencode, urljoin
from defusedxml.ElementTree import fromstring, ParseError
from django.utils.functional import cached_property
from django.utils.text import slugify
import requests
from zentral.core.events import event_from_event_d
from zentral.core.stores.backends.base import BaseEventStore


logger = logging.getLogger('zentral.core.stores.backends.splunk')


class EventStore(BaseEventStore):
    max_batch_size = 100
    max_retries = 3

    def __init__(self, config_d):
        super().__init__(config_d)
        self.collector_url = urljoin(config_d["hec_url"], "/services/collector/event")
        self.hec_token = config_d["hec_token"]
        self.search_app_url = config_d.get("search_app_url")
        # If set, the computer name of the machine snapshots of these sources will be used
        # as host field value. First source with a non-empty value will be picked.
        self.computer_name_as_host_sources = [
            slugify(src)
            for src in config_d.get("computer_name_as_host_sources", [])
        ]
        self.serial_number_field = config_d.get("serial_number_field", "machine_serial_number")
        if self.search_app_url:
            self.machine_events_url = True
            self.probe_events_url = True
        self.verify_tls = config_d.get('verify_tls', True)
        self.index = config_d.get("index")
        self.source = config_d.get("source")
        # search
        self.authentication_token = config_d.get("authentication_token")
        self.search_url = config_d.get("search_url")
        self.search_source = config_d.get("search_source")
        self.search_timeout = int(config_d.get("search_timeout", 300))
        if self.search_url and self.authentication_token:
            self.machine_events = True
            self.probe_events = True

    @cached_property
    def collector_session(self):
        session = requests.Session()
        session.verify = self.verify_tls
        session.headers.update({'Authorization': f'Splunk {self.hec_token}',
                                'Content-Type': 'application/json'})
        return session

    @staticmethod
    def _convert_datetime(dt):
        if isinstance(dt, str):
            dt = dt.replace("+00:00", "").replace("Z", "").strip()
            if "." in dt:
                fmt = "%Y-%m-%dT%H:%M:%S.%f"
            else:
                fmt = "%Y-%m-%dT%H:%M:%S"
            dt = datetime.strptime(dt, fmt)
        ts = time.mktime(dt.timetuple()) + dt.microsecond / 1e6
        return "{:.3f}".format(ts)

    def _serialize_event(self, event):
        if not isinstance(event, dict):
            event = event.serialize()
        payload_event = event.pop("_zentral")
        created_at = payload_event.pop("created_at")
        event_type = payload_event.pop("type")
        namespace = payload_event.get("namespace", event_type)
        payload_event[namespace] = event
        # host / serial number
        host = "Zentral"
        machine_serial_number = payload_event.pop("machine_serial_number", None)
        if machine_serial_number:
            payload_event[self.serial_number_field] = machine_serial_number
            host = machine_serial_number
            for ms_src_slug in self.computer_name_as_host_sources:
                machine_name = payload_event.get("machine", {}).get(ms_src_slug, {}).get("name")
                if machine_name:
                    host = machine_name
                    break
        else:
            observer = payload_event.get("observer", {}).get("hostname")
            if observer:
                host = observer
        payload = {
            "host": host,
            "sourcetype": event_type,
            "time": self._convert_datetime(created_at),
            "event": payload_event,
        }
        if self.index:
            payload["index"] = self.index
        if self.source:
            payload["source"] = self.source
        return payload

    def _deserialize_event(self, result):
        metadata = json.loads(result["_raw"])
        # normalize serial number
        if self.serial_number_field in metadata:
            metadata["machine_serial_number"] = metadata.pop(self.serial_number_field)
        # add created at
        metadata["created_at"] = result["_time"]
        # event type
        event_type = result["sourcetype"]
        metadata["type"] = event_type
        # event data
        namespace = metadata.get("namespace", event_type)
        event_d = metadata.pop(namespace)
        event_d["_zentral"] = metadata
        return event_from_event_d(event_d)

    def store(self, event):
        payload = self._serialize_event(event)
        for i in range(self.max_retries):
            r = self.collector_session.post(self.collector_url, json=payload)
            if r.ok:
                return
            if r.status_code > 500:
                logger.error("Temporary server error")
                if i + 1 < self.max_retries:
                    seconds = random.uniform(3, 4) * (i + 1)
                    logger.error("Retry in %.1fs", seconds)
                    time.sleep(seconds)
                    continue
            r.raise_for_status()

    def bulk_store(self, events):
        if self.batch_size < 2:
            raise RuntimeError("bulk_store is not available when batch_size < 2")
        event_keys = []
        data = b""
        for event in events:
            payload = self._serialize_event(event)
            event_keys.append((payload["event"]["id"], payload["event"]["index"]))
            if data:
                data += b"\n"
            data += json.dumps(payload).encode("utf-8")
        for i in range(self.max_retries):
            r = self.collector_session.post(self.collector_url, data=data)
            if r.ok:
                return event_keys
            if r.status_code > 500:
                logger.error("Temporary server error")
                if i + 1 < self.max_retries:
                    seconds = random.uniform(3, 4) * (i + 1)
                    logger.error("Retry in %.1fs", seconds)
                    time.sleep(seconds)
                    continue
            r.raise_for_status()

    # event methods

    @cached_property
    def search_session(self):
        session = requests.Session()
        session.verify = self.verify_tls
        session.headers.update({'Authorization': f'Bearer {self.authentication_token}',
                                'Content-Type': 'application/json'})
        return session

    def _build_filters(self, event_type=None, serial_number=None):
        filters = []
        if self.index:
            filters.append(("index", self.index))
        if self.search_source:
            filters.append(("source", self.search_source))
        if event_type:
            filters.append(("sourcetype", event_type))
        if serial_number:
            if not self.computer_name_as_host_sources:
                filters.append(("host", serial_number))
            else:
                filters.append((self.serial_number_field, serial_number))
        return " ".join('{}="{}"'.format(k, v.replace('"', '\\"')) for k, v in filters)

    def _get_search_url(self, query, from_dt, to_dt):
        kwargs = {
            "q": f"search {query}",
            "earliest": self._convert_datetime(from_dt),
            "latest": self._convert_datetime(to_dt) if to_dt else "now"
        }
        return "{}?{}".format(self.search_app_url, urlencode(kwargs))

    def _post_search_job(self, search, from_dt, to_dt):
        data = {"exec_mode": "blocking",
                "id": str(uuid.uuid4()),
                "search": f"search {search}",
                "earliest_time": from_dt.isoformat(),
                "timeout": self.search_timeout}
        if to_dt:
            data["latest_time"] = to_dt.isoformat()
        r = self.search_session.post(
            urljoin(self.search_url, "/services/search/jobs"),
            data=data
        )
        r.raise_for_status()
        try:
            response = fromstring(r.content)
        except ParseError:
            raise
        return response.find("sid").text

    def _get_search_results(self, sid, offset=0, count=100000):
        r = self.search_session.get(
            urljoin(self.search_url, f"/services/search/jobs/{sid}/results"),
            params={"offset": offset, "count": count, "output_mode": "json"}
        )
        r.raise_for_status()
        return r.json()

    def _fetch_aggregated_event_counts(self, query, from_dt, to_dt):
        sid = self._post_search_job(f"{query} | stats count by sourcetype", from_dt, to_dt)
        results = self._get_search_results(sid)
        return {r["sourcetype"]: int(r["count"]) for r in results["results"]}

    def _fetch_events(self, query, from_dt, to_dt, limit, cursor):
        if cursor is None:
            sid = self._post_search_job(query, from_dt, to_dt)
            offset = 0
        else:
            sid, offset = cursor.split("$")
            offset = int(offset)
        events = []
        new_cursor = None
        results = self._get_search_results(sid, offset, limit)
        init_offset = results["init_offset"]
        result_count = 0
        for result in results["results"]:
            result_count += 1
            events.append(self._deserialize_event(result))
        if result_count >= limit:
            new_offset = init_offset + result_count
            new_cursor = f"{sid}${new_offset}"
        return events, new_cursor

    # machine events

    def _get_machine_events_query(self, serial_number, event_type=None):
        return self._build_filters(event_type, serial_number)

    def fetch_machine_events(self, serial_number, from_dt, to_dt=None, event_type=None, limit=10, cursor=None):
        return self._fetch_events(
            self._get_machine_events_query(serial_number, event_type),
            from_dt, to_dt, limit, cursor
        )

    def get_aggregated_machine_event_counts(self, serial_number, from_dt, to_dt=None):
        return self._fetch_aggregated_event_counts(
            self._get_machine_events_query(serial_number),
            from_dt, to_dt
        )

    def get_machine_events_url(self, serial_number, from_dt, to_dt=None, event_type=None):
        return self._get_search_url(
            self._get_machine_events_query(serial_number, event_type),
            from_dt, to_dt
        )

    # probe events

    def _get_probe_events_query(self, probe, event_type=None):
        filters = self._build_filters(event_type)
        return f'{filters} | spath "probes{{}}.pk" | search "probes{{}}.pk"={probe.pk}'

    def get_aggregated_probe_event_counts(self, probe, from_dt, to_dt=None):
        return self._fetch_aggregated_event_counts(
            self._get_probe_events_query(probe),
            from_dt, to_dt
        )

    def fetch_probe_events(self, probe, from_dt, to_dt=None, event_type=None, limit=10, cursor=None):
        return self._fetch_events(
            self._get_probe_events_query(probe, event_type),
            from_dt, to_dt, limit, cursor
        )

    def get_probe_events_url(self, probe, from_dt, to_dt=None, event_type=None):
        return self._get_search_url(
            self._get_probe_events_query(probe, event_type),
            from_dt, to_dt
        )
