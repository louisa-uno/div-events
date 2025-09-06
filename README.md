# .ICS calendars for Diversity München Events
[![Action Status: create-calendars.yml](https://github.com/louisa-uno/div-events/actions/workflows/update-db.yml/badge.svg)](https://github.com/louisa-uno/div-events/actions/workflows/update-db.yml)
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
| JuLes              | jl   | [jl.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendarsjl.ics) |
| Wilma              | wi   | [wi.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendarswi.ics) |
| frients            | ff   | [ff.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendarsff.ics) |
| youngsters         | yo   | [yo.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendarsyo.ics) |
| JUNGS              | jn   | [jn.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendarsjn.ics) |
| plusPOL            | pp   | [pp.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendarspp.ics) |
| NoDifference!      | nd   | [nd.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendarsnd.ics) |
| refugees@diversity | re   | [re.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendarsre.ics) |
| DINOs              | di   | [di.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendarsdi.ics) |
| bi.yourself        | bi   | [bi.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendarsbi.ics) |
| enBees             | en   | [en.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendarsen.ics) |
| diversity@school   | ds   | [ds.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendarsds.ics) |
| QueerBeats         | qb   | [qb.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendarsqb.ics) |
| queer-to-queer     | qq   | [qq.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendarsqq.ics) |
| diversity München  | dm   | [dm.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendarsdm.ics) |
| AroSpAce           | as   | [as.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendarsas.ics) |
| BiPoC-Abend        | bp   | [bp.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendarsbp.ics) |
| Non Organizer      | no   | [no.ics](https://raw.githubusercontent.com/louisa-uno/div-events/refs/heads/auto-update/calendarsno.ics) |

### Combined Group calendars 
Combine group calendars into a single calendar by joining their codes with a hyphen and appending .ics
Base URL: https://div-events.cdnapp.de/
Pattern: "https://div-events.cdnapp.de/" + group_code + "-" + group_code + ".ics"
Example: For jl and wi → https://div-events.cdnapp.de/jl-wi.ics