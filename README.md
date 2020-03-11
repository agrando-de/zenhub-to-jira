# zenhub-to-jira
Export zenhub boards to JIRA CSV format


## Gotchas:
* 03.2020: JIRA has two importers that have different functionality:
  * Inside of a project, click the '+' on the sidebar, at the top-right of the modal, click 'Import Issues'
    * This importer does not allow Status or Comments to be imported
      * It's suggested to instead append comments to the Description field (as this script does)
      * For Status, it's suggested to import issues and once done, arrange their statuses to match the current state of Zenhub. It's a bit of a pain, but better than the other importer
  * Inside of admin settings, click System -> External System Import
    * This importer does not correctly map issue types. It converts everything to a story, even if you specify the mapping of Epic -> Epic, Task -> Task, etc., it does not work
