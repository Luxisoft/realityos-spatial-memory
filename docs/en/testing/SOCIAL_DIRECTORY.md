[Español](../../es/testing/SOCIAL_DIRECTORY.md) · [API / Postman](../api/API.md) · [Documentation](../INDEX.md)

# Local social directory

Meta Social Media has ten synthetic searchable profiles, each with a separate avatar and three private reference photos. Its three access accounts publish one ordinary introduction each using their account avatars. The group also contains three ordinary video publications. Private references never appear as publications, generic media or result thumbnails.

Profile rows are installed from the versioned [social SQL seed](../../../simulator/database/002-social-profiles.sql). The local bootstrap uses the existing protected enrollment workflow and records its completion once. Restarts preserve edits and deletions. Group membership, consent and biometric permissions continue to apply; installing test data does not authorize other accounts or new subjects.

| Location | Purpose |
| --- | --- |
| [Avatars](../../../simulator/media/meta-social/avatars/) | Separate images that may be displayed as profile avatars. |
| [Private references](../../../simulator/media/meta-social/private-references/) | Three distinct references for each prepared synthetic profile. |
| [Shared account avatars](../../../simulator/media/shared/accounts/) | Images for the nine local access accounts. |
| [Media manifest](../../../simulator/media/manifest.csv) | Source, license and SHA-256 evidence for organized local resources. |

The application reads profiles, membership and publications from PostgreSQL. No JSON directory or parallel publication catalog serves queries. The SQL seed is an installation input; subsequent changes use the application tables and APIs.

Historical graphics retained for regression tests are under `simulator/media/regression/`. They do not create retired groups or additional profiles. The current local scope remains Police, Meta Social Media and Memory.
