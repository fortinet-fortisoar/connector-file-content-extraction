# File Content Extraction
 The connector uses Apache Tika to extract content and artifacts from almost any file

## Prerequisites
The connector requires python tika `sudo -u nginx /opt/cyops-integrations/.env/bin/pip install -r /opt/cyops-integrations/integrations/connectors/file-content-extraction_1_0_0/requirements.txt`

## Usage

The connector includes the playbook: `Extract and Process Text From File` which can be used with any file to extract its content, metadata and artifacts. Simply run the playbook, the result will be shown in filePreview field if your indicators module has it, otherwise the result will be added to the indicator description