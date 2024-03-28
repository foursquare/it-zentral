from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from .api_views import (ArtifactDetail, ArtifactList,
                        BlueprintDetail, BlueprintList,
                        BlueprintArtifactDetail, BlueprintArtifactList,
                        EnterpriseAppDetail, EnterpriseAppList,
                        EnrolledDeviceList,
                        LocationList,
                        LockEnrolledDevice, EraseEnrolledDevice,
                        FileVaultConfigDetail, FileVaultConfigList,
                        ProfileDetail, ProfileList,
                        RecoveryPasswordConfigList, RecoveryPasswordConfigDetail,
                        SoftwareUpdateEnforcementList, SoftwareUpdateEnforcementDetail,
                        DEPVirtualServerSyncDevicesView,
                        EnrolledDeviceFileVaultPRK, EnrolledDeviceRecoveryPassword,
                        SyncSoftwareUpdatesView)


app_name = "mdm_api"
urlpatterns = [
    path('artifacts/', ArtifactList.as_view(), name="artifacts"),
    path('artifacts/<uuid:pk>/', ArtifactDetail.as_view(), name="artifact"),
    path('blueprints/', BlueprintList.as_view(), name="blueprints"),
    path('blueprints/<int:pk>/', BlueprintDetail.as_view(), name="blueprint"),
    path('blueprint_artifacts/', BlueprintArtifactList.as_view(), name="blueprint_artifacts"),
    path('blueprint_artifacts/<int:pk>/', BlueprintArtifactDetail.as_view(), name="blueprint_artifact"),
    path('enterprise_apps/', EnterpriseAppList.as_view(), name="enterprise_apps"),
    path('enterprise_apps/<uuid:artifact_version_pk>/', EnterpriseAppDetail.as_view(), name="enterprise_app"),
    path('filevault_configs/', FileVaultConfigList.as_view(), name="filevault_configs"),
    path('filevault_configs/<int:pk>/', FileVaultConfigDetail.as_view(), name="filevault_config"),
    path('locations/', LocationList.as_view(), name="locations"),
    path('profiles/', ProfileList.as_view(), name="profiles"),
    path('profiles/<uuid:artifact_version_pk>/', ProfileDetail.as_view(), name="profile"),
    path('recovery_password_configs/', RecoveryPasswordConfigList.as_view(), name="recovery_password_configs"),
    path('recovery_password_configs/<int:pk>/', RecoveryPasswordConfigDetail.as_view(),
         name="recovery_password_config"),
    path('software_update_enforcements/', SoftwareUpdateEnforcementList.as_view(),
         name="software_update_enforcements"),
    path('software_update_enforcements/<int:pk>/', SoftwareUpdateEnforcementDetail.as_view(),
         name="software_update_enforcement"),

    path('dep/virtual_servers/<int:pk>/sync_devices/',
         DEPVirtualServerSyncDevicesView.as_view(), name="dep_virtual_server_sync_devices"),
    path('devices/', EnrolledDeviceList.as_view(), name="enrolled_devices"),
    path('devices/<int:pk>/erase/', EraseEnrolledDevice.as_view(), name="erase_enrolled_device"),
    path('devices/<int:pk>/lock/', LockEnrolledDevice.as_view(), name="lock_enrolled_device"),
    path('devices/<int:pk>/filevault_prk/', EnrolledDeviceFileVaultPRK.as_view(),
         name="enrolled_device_filevault_prk"),
    path('devices/<int:pk>/recovery_password/', EnrolledDeviceRecoveryPassword.as_view(),
         name="enrolled_device_recovery_password"),
    path('software_updates/sync/',
         SyncSoftwareUpdatesView.as_view(), name="sync_software_updates"),
]


urlpatterns = format_suffix_patterns(urlpatterns)
