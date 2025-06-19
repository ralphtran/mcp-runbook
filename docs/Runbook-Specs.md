# `Runbook.yaml` Specification v0.1

This document specifies the structure for a `runbook.yaml` file. The file defines a collection of automated, multi-step tools that can be executed by a local runner. The design prioritizes simplicity, human readability, and a secure, `keyring`-based secret management workflow.

## Root Object

The root of the YAML file must be a dictionary containing the following keys:

| Key       | Type                    | Required? | Description                                             |
|-----------|-------------------------|-----------|---------------------------------------------------------|
| `version` | `string`                | **Yes**   | The version of this configuration file's schema.        |
| `tools`   | `list` of `Tool Object` | **Yes**   | The main list of available tools.                       |

### Example:
```yaml
# tools.yaml
version: "0.1"
tools:
  - # ... Tool Object 1 ...
  - # ... Tool Object 2 ...
```

---

## The Tool Object

Each item in the `tools` list is a dictionary representing a single, runnable tool.

| Key           | Type                      | Required? | Description                                                                            |
|---------------|---------------------------|-----------|----------------------------------------------------------------------------------------|
| `name`        | `string`                  | **Yes**   | A unique, machine-friendly identifier for the tool (e.g., `publish-package`).          |
| `description` | `string`                  | **Yes**        | A clear, natural language description of what the tool accomplishes as a whole.        |
| `steps`       | `list` of `Step Object`   | **Yes**   | A list of command steps to be executed sequentially.                                   |
| `parameters`  | `dictionary`              | No        | A dictionary defining the parameters the tool accepts.                                 |
| `secrets`     | `list` of `Secret Object` | No        | A list of secrets required by the tool, fetched from the system keyring.               |
| `cwd`         | `string`                  | No        | The default working directory for all steps. Can be overridden in a specific step.     |
| `timeout`     | `integer`                 | No        | The total maximum time in seconds for the entire tool to run before being terminated.  |

---

## Field Details

### `steps` (list of `Step Object`)

This is the core execution logic of a tool. Each item in the list is a **Step Object** that is executed in order. If any step fails, the entire tool execution stops.

#### The Step Object

| Key       | Type         | Required? | Description                                                               |
|-----------|--------------|-----------|---------------------------------------------------------------------------|
| `name`    | `string`     | **Yes**   | A short, human-readable name for the step (e.g., "Install Dependencies"). |
| `command` | `string`     | **Yes**   | A multi-line shell script to be executed.                                 |
| `cwd`     | `string`     | No        | Overrides the tool's default working directory for this specific step.    |
| `env`     | `dictionary` | No        | Non-sensitive environment variables specific to this step.                |

### `parameters` (dictionary)

Defines the inputs for the tool. The key is the parameter name (used for substitution like `{param_name}` in commands), and the value is a dictionary specifying its details:

| Key           | Type        | Required? | Description                                                   |
|---------------|-------------|-----------|---------------------------------------------------------------|
| `description` | `string`    | **Yes**   | Explains what the parameter is for.                           |
| `type`        | `string`    | No        | Data type for basic validation. Defaults to `string`.         |
| `required`    | `boolean`   | No        | Whether this parameter must be provided. Defaults to `false`. |
| `default`     | `any`       | No        | A default value to use if the parameter is not provided.      |

### `secrets` (list of `Secret Object`)

Defines secrets to be securely fetched from the system `keyring` and injected as environment variables for the tool's subprocess.

#### The Secret Object

| Key      | Type     | Required? | Description                                                              |
|----------|----------|-----------|--------------------------------------------------------------------------|
| `source` | `string` | **Yes**   | The **profile name** of the secret to look up in the system keyring.     |
| `target` | `string` | **Yes**   | The name of the environment variable the secret will be assigned to.     |

---

## Complete `runbook.yaml` Example

```yaml
version: "0.1"
tools:
  
  - name: "publish-npm-package"
    description: "Builds and publishes an NPM package to the registry. Requires an NPM automation token."
    timeout: 300

    parameters:
      version_bump:
        description: "The version to bump to (e.g., 'patch', 'minor', 'major')."
        required: true
        default: "patch"

    secrets:
      # This tool needs one secret from the keyring.
      # It will look for a profile named 'npm-automation-token' and expose it
      # as the NPM_TOKEN environment variable to the commands below.
      - source: "npm-automation-token"
        target: "NPM_TOKEN"
    
    steps:
      - name: "Install dependencies"
        command: |
          echo "Installing NPM dependencies..."
          npm install

      - name: "Bump version and publish"
        command: |
          echo "Publishing new version: {version_bump}"
          # The NPM_TOKEN env var is automatically used by 'npm publish'
          npm version {version_bump}
          npm publish

  - name: "backup-database-to-s3"
    description: "Dumps a local PostgreSQL database and uploads it to an AWS S3 bucket. Requires DB password and AWS credentials."

    parameters:
      db_name:
        description: "The name of the PostgreSQL database to back up."
        required: true
      s3_bucket_path:
        description: "The full S3 path for the backup file (e.g., 'my-backups/prod/db.sql.gz')."
        required: true

    secrets:
      # This tool needs multiple secrets, all sourced from the local keyring.
      - source: "local-postgres-password"
        target: "PGPASSWORD" # pg_dump automatically uses this env var
      - source: "aws-access-key-id"
        target: "AWS_ACCESS_KEY_ID"
      - source: "aws-secret-access-key"
        target: "AWS_SECRET_ACCESS_KEY"

    steps:
      - name: "Dump database and upload"
        command: |
          echo "Backing up database '{db_name}' to S3..."
          
          # The AWS CLI will automatically use the AWS_* environment variables.
          # The pg_dump command will automatically use the PGPASSWORD variable.
          pg_dump -U postgres -h localhost {db_name} | gzip | aws s3 cp - s3://{s3_bucket_path}

          echo "Backup complete!"
```
