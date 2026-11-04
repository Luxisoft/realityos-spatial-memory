[Español](../../es/testing/SOCIAL_DIRECTORY.md) · [API / Postman](../api/API.md) · [Documentation](../INDEX.md)

# Local social directory

Meta Social Media has thirteen synthetic searchable profiles, each with a separate avatar and three private reference photos. Its three access accounts publish one ordinary introduction each using their account avatars. The group also contains three ordinary video publications. Private references never appear as publications, generic media or result thumbnails.

Profile rows are installed from the versioned [initial social SQL](../../../simulator/database/002-social-profiles.sql) and [three-profile addition](../../../simulator/database/006-social-profiles.sql). The local bootstrap uses the existing protected enrollment workflow and records each revision once. Restarts preserve edits and deletions. Group membership, consent and biometric permissions continue to apply; installing test data does not authorize other accounts or new subjects.

The addition contains Gabriel Herrera, Adrián Navarro and Paula Méndez. Each supplied avatar has three distinct private references generated with the built-in image tool while preserving its character's identity, in park, terrace café and window-lit interior scenes. Provenance and hashes remain in the media manifest. The full directory has thirteen display avatars and thirty-nine private references; none of the new profiles expands the six-account selector.

| Location | Purpose |
| --- | --- |
| [Avatars](../../../simulator/media/meta-social/avatars/) | Separate images that may be displayed as profile avatars. |
| [Private references](../../../simulator/media/meta-social/private-references/) | Three distinct references for each prepared synthetic profile. |
| [Shared account avatars](../../../simulator/media/shared/accounts/) | Images for the six local access accounts. |
| [Media manifest](../../../simulator/media/manifest.csv) | Source, license and SHA-256 evidence for organized local resources. |

The application reads profiles, membership and publications from PostgreSQL. No JSON directory or parallel publication catalog serves queries. The SQL seed is an installation input; subsequent changes use the application tables and APIs.

Historical graphics retained for regression tests are under `simulator/media/regression/`. They do not create retired groups or additional profiles. The current local scope remains Police and Meta Social Media.
