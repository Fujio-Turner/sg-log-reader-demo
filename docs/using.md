
### Getting the Dashboard

To get to a dashboard to see stats you'll run a local python Flask Web Server. Run the Command below to start the web server.

```console
# python3 app.py config.json
```

OUTPUT should look something like this.

```console
 * Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8080
 * Running on http://192.168.0.193:8080
```

Now open up your web browser and go to: [http://127.0.0.1:8080](http://127.0.0.1:8080)


Just click the button(`Search`) you should get some results.

* The dashboard will auto pre-populate 
   - FROM DateTime input box (newest time record in the `sg_info.log` file) 
   - TO DateTime input box , an hour back from the above DateTime.
   - It will pre select a SG DB name too.


### Dashboard Navigation

##### Zoom-In & Pan (drag: left or right) - Charts
You can click on the line charts and PAN left or right by dragging it. If you hold down the `SHIFT` and select in the chart it will create a `zoom` box for you pick a section of the chart your more interesting in. There is a `Zoom Reset` button on the left. The two line charts will adjust themselves to the new x-axis on zoom and/or pan too.

#### Picking a Specific User

##### User List:

On the left it will show you all the SG users who made connections in the DatesTime window selected above plus how many times they connected in that time window. 
You can sort the list alphabetically(default) or by most number of connections.

##### Just Click User Name:
Just click the name of the user and it will pre populate the filter by username input box ,above, and then just click `Search` to filter and populate charts and stats for that user only.

***note*** When you pick and `Search` by a users the chart will plot `All Entries` on the x-axis regardless if you didn't change the `view by` dropdown value.

##### User Details:

Once you `Search` by a user on the bottom it will show you all the indivudal replication events for that user for that DateTime. If you click on the row it will show the full raw SG log for the WebSocket ID.
