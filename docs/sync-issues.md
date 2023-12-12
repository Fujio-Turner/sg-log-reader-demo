
### Common Reasons Why Docs Don't Sync
1. The CBL user ,at the time of sync, was not assigned access to read a particular channel(s) the document(s) are on.

2. The user roles was not set correctly or role was deleted

3. Document was not on the channel(s) when the user last syncs

4. Document is set on the channels in the beginning , but later or in the middle of multipe updates the channel was unassigend
    - JSON element in the document with the channel info is missing during document updates.

5. There is a conflict in the document and the device decides not to sync it. Rules on [default conflict resolution in CBL](https://docs.couchbase.com/couchbase-lite/current/c/conflict.html#automatic-conflict-resolution)

6. Couchbase Lite Deletes/Purges/Expires(TTLs) docs locally , but the next time CBL syncs the docs at SG never changed.



### Not So Common Reasons Why Docs Don't Sync

1. Starting multiples of the same exact replicator all at once leading to a fight by the replicators on getting/setting the same checkpoint.

<img src="img/spiderman-meme.png" alt="Couchbase Lite Replicators" height="250px">


2. Load Balancer or Security Device killing the Websocket connection before the 5 minute keepalive is sent from CBL.

3. Deleting SG users while the user is replicating, but re-creating the same user later.

4. Starting to many replicators on the device. Example: You have a CBL replicator per single channel , but there are 20-80 channels.

<img src="img/everybody-gets-a-replicator.jpeg" alt="Couchbase Lite Replicators per channel" height="230px">