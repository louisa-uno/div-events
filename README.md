# .ICS calendars for Diversity München Events
[![Action Status: update-db.yml](https://github.com/louisa-uno/div-events/actions/workflows/update-db.yml/badge.svg)](https://github.com/louisa-uno/div-events/actions/workflows/update-db.yml)
[![Action Status: create-calendars.yml](https://github.com/louisa-uno/div-events/actions/workflows/create-calendars.yml/badge.svg)](https://github.com/louisa-uno/div-events/actions/workflows/create-calendars.yml)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL–3.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0.html)

Provides .ICS calendars for the events [diversity München](https://diversity-muenchen.de) lists on their website
## Calendar types
### General calendar
A calendar with all the events
[all.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/all.ics)
### Group calendars
Calendars for each of the diversity groups

| Name               | Code | Link                                                                                                     |
| ------------------ | ---- | -------------------------------------------------------------------------------------------------------- |
| JuLes              | jl   | [jl.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendars/jl.ics) |
| Wilma              | wi   | [wi.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendars/wi.ics) |
| frients            | ff   | [ff.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendars/ff.ics) |
| youngsters         | yo   | [yo.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendars/yo.ics) |
| JUNGS              | jn   | [jn.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendars/jn.ics) |
| plusPOL            | pp   | [pp.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendars/pp.ics) |
| NoDifference!      | nd   | [nd.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendars/nd.ics) |
| refugees@diversity | re   | [re.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendars/re.ics) |
| DINOs              | di   | [di.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendars/di.ics) |
| bi.yourself        | bi   | [bi.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendars/bi.ics) |
| enBees             | en   | [en.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendars/en.ics) |
| diversity@school   | ds   | [ds.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendars/ds.ics) |
| QueerBeats         | qb   | [qb.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendars/qb.ics) |
| queer-to-queer     | qq   | [qq.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendars/qq.ics) |
| diversity München  | dm   | [dm.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendars/dm.ics) |
| AroSpAce           | as   | [as.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendars/as.ics) |
| BiPoC-Abend        | bp   | [bp.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendars/bp.ics) |
| Non Organizer      | no   | [no.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendars/no.ics) |

### Combined Group calendars
Combine group calendars into a single calendar by joining their codes with a hyphen and appending .ics

Base URL: https://div-events.cdnapp.de/

Pattern: "https://div-events.cdnapp.de/" + group_code + "-" + group_code + ".ics"

Example: For jl and wi → https://div-events.cdnapp.de/jl-wi.ics
