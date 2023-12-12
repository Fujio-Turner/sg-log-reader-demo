## Step 1. - Requirements
### Requirements:

- Python 3.6 or greater

- Couchbase Cluster 7.x with Index & Query Services

- Couchbase Bucket (named: `sg-log-reader._default._default`)

- Create the below indexes.

```sql
CREATE INDEX `sgProcessErrorsEpoch_v4` ON `sg-log-reader`(`dtFullEpoch`,`import`,`dcp`,`query`,`sgDb`,`ws`,`gen`) WHERE (`docType` = "sgErrors")
```

```sql
CREATE INDEX `userSyncFinderEpoch_v7` ON `sg-log-reader`(`dtFullEpoch`,`user`,`sgDb`,`dtDiffSec`,`sentCount`,`errors`,`tRow`,`since`,array_length(`filterBy`),`conflicts`,`pushAttCount`,`pullAttCount`,`pushCount`,`qRow`,`cRow`,`blipC`) WHERE ((`docType` = "byWsId") and (`orphane` = false))
```