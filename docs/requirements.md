## Step 1. - Requirements
### Requirements:

- Couchbase Cluster 7.x with Index & Query Services

- Couchbase Bucket (named: `sg-log-reader._default._default`)

- Create the below indexes.

```sql
CREATE INDEX `sgProcessErrorsEpoch_v4` ON `sg-log-reader`(`dtFullEpoch`,`import`,`dcp`,`query`,`sgDb`,`ws`,`gen`) WHERE (`docType` = "sgErrors")
```

```sql
CREATE INDEX `userSyncFinderEpoch_v8` ON `sg-log-reader`(`dtFullEpoch`,`user`,`sgDb`,`dtDiffSec`,`sentCount`,`errors`,`tRow`,`since`,array_length(`filterBy`),`conflicts`,`pushAttCount`,`pullAttCount`,`pushCount`,`qRow`,`cRow`,`blipC`,`warnings`) WHERE ((`docType` = "byWsId") and (`orphane` = false))
```