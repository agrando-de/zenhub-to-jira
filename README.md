# zenhub-to-jira
Export zenhub boards to JIRA CSV format


## Gotchas:
* This script can import issues marked as Done, but this becomes much more of a pain, so that functionality has been commented out. It's suggested to only import current / backlog issues.
* When mapping labels, if you don't want to import a label and map it to blank, the label will still be imported. Instead, you should modify the script so it does not include the label.
* 03.2020: JIRA has two importers that have different functionality:
  * Inside of a project, click the '+' on the sidebar, at the top-right of the modal, click 'Import Issues'
    * This importer does not allow Status or Comments to be imported
      * It's suggested to instead append comments to the Description field (as this script does)
      * For Status, it's suggested to import issues and once done, arrange their statuses to match the current state of Zenhub. It's a bit of a pain, but better than the other importer
  * Inside of admin settings, click System -> External System Import
    * This importer does not correctly map issue types. It converts everything to a story, even if you specify the mapping of Epic -> Epic, Task -> Task, etc., it does not work
