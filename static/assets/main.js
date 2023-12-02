sgName = ""
viewByValue = ""

$('#dtFrom').on('input',function(e){

  var from = $('#dtFrom').val();
    var to = $('#dtTo').val();
    if(from === "" || to === ""){
      $.notify("Pick a Date Range");
      return;
    }
    if(sgName === ""){
      sgDbListGet();
    }
});


$('#dtTo').on('input',function(e){

   var from = $('#dtFrom').val();
    var to = $('#dtTo').val();
    if(from === "" || to === ""){
      $.notify("Pick a Date Range");
      return;
    }

    if(sgName === ""){
      sgDbListGet();
    }
});


$('#sgDbListOptions').on('input',function(e){
  sgName = $('#sgDbListOptions').val();
});


$('input[type=radio][name=userSort]').change(function() {
    sgUserList()
});

$("#searchByUser").on("input", function(){
    
  /*
      if($("#searchByUser").val() == ''){
          console.log(viewByValue)
        $("#viewBy").prop("disabled", false);
        $("#viewBy").val(viewByValue).change()
      }else{
        $("#viewBy").prop("disabled", true);
        viewByValue =  $("#viewBy").val()
      }
      */
    });


  $("#resetFilters").click(function(e){
    $("#syncResult").val('any');
    $("#noPushes").val('any');
    $("#changeCount").val("");
    $("#syncTime").val("");
    $("#sinceZero").prop('checked', false);
    $("#errors").prop('checked', false);
    $("#conflicts").prop('checked', false);
    $("#filterByChannels").prop('checked', false);
    $('#hasAttachments').prop('checked', false);
    $('#hasPullAttachments').prop('checked', false);
  });

$(document).ready(function(){

getSampleDt()

$('#wsDetails').hide();


$("#userSyncStatsTable").on("click", "tr", function() {
    var ws = $(this).find("td").eq(1).text();
    console.log(ws);
   $.notify("WebSocket Details for: "+ws,'success')
    userSyncDetails(ws)
    $('#wsDetails').show('slow');
  });



dtConfig = {
  format:'YYYY-MM-DDTHH:mm:ss',
  time: {
		enabled: true
	},
  showShortcuts: true,
  customShortcuts: 
	[
  {
			name: 'last 24hr',
			dates : function()
			{
				var start = moment().day(0).toDate();
				var end = moment().day(1).toDate();
				return [start,end];
			}
		},
		{
			name: 'this week',
			dates : function()
			{
				var start = moment().day(0).toDate();
				var end = moment().day(6).toDate();
				return [start,end];
			}
		}
	],
  separator : ' to ',
	getValue: function()
	{
		if ($('#dtFrom').val() && $('#dtTo').val() )
			return $('#dtFrom').val() + ' to ' + $('#dtTo').val();
		else
			return '';
	},
	setValue: function(s,s1,s2)
	{
		$('#dtFrom').val(s1);
		$('#dtTo').val(s2);
	}

}

$('#dtFrom').dateRangePicker(dtConfig);
$('#dtTo').dateRangePicker(dtConfig);

});


function sgDbListGet(){
  $('#sgDbListOptions').empty()
  var data1 = {}
  var to = $('#dtTo').val();
  var from = $('#dtFrom').val();
  data1['startDt'] = from
  data1['endDt'] = to
  data1["startDtEpoch"] = Math.floor(new Date(from).getTime() / 1000)
  data1["endDtEpoch"] = Math.floor(new Date(to).getTime() / 1000)

    $.ajax({
      type: 'POST',
      url: '/sgDbListEpoch',
      data: JSON.stringify(data1),
      dataType: 'json',
      contentType:'application/json; charset=utf-8',
      success: function(data2) { 
        
        $.each(data2, function(key, value) {       
            if(key === 0){
              var html = '<option value="'+value.sgDb+'" selected>'+value.sgDb+'</option>';
              sgName = value.sgDb
            }else{
              var html = '<option value="'+value.sgDb+'" >'+value.sgDb+'</option>';              
            }              
            $("#sgDbListOptions").append(html)
          });
          $.notify("Find SG DBs","success");
      }
  });
}


function sgUserList(){
  $('#sgUserListSelect').empty()

  var from = $('#dtFrom').val();
  var to = $('#dtTo').val();
    
  var data1 = {}
  data1["sgDb"] = $('#sgDbListOptions').val()
  data1['startDt'] = from
  data1['endDt'] = to
  data1["startDtEpoch"] = Math.floor(new Date(from).getTime() / 1000)
  data1["endDtEpoch"] = Math.floor(new Date(to).getTime() / 1000)
  data1['sortBy'] = $('input[name="userSort"]:checked').val();

  data1["syncResult"] = $("#syncResult").val();
  data1["changeCount"] = $('#changeCount').val()
  data1["syncTime"] = $('#syncTime').val()
  data1["filterByChannels"] = $('#filterByChannels').is(":checked");
  data1["conflicts"] = $('#conflicts').is(":checked");
  data1["sinceZero"] = $('#sinceZero').is(":checked");
  data1["errors"] = $('#errors').is(":checked");
  data1["noPushes"] = $('#noPushes').val();
  data1["attachments"] = $('#hasAttachments').is(":checked")
  data1["attachmentsPull"] = $('#hasPullAttachments').is(":checked")


  $.ajax({
    type: 'POST',
    url: '/sgUserListEpoch',
    data: JSON.stringify(data1),
    dataType: 'json',
    contentType:'application/json; charset=utf-8',
    success: function(data2) { 
      var userCount = 0
          $.each(data2, function(key, value) {
            userCount++

            var c = "dark"
          if(key % 2 == 0) {
            c = "light"
            }
          var option1 = '<option class="ws-'+c+'" onclick="userFill(\''+value.user+'\')"  >' +value.user+ ' ('+value.sgUserCount+')</option>'

          $('#sgUserListSelect').append(option1)
        });

        $("#userListTotalCount").html(userCount)
        }
    });
  }

  function sgErrorGraph(){

    var from = $('#dtFrom').val();
    var to = $('#dtTo').val();
    

    var data1 = {}
    data1['startDt'] = from
    data1['endDt'] = to
    data1["startDtEpoch"] = Math.floor(new Date(from).getTime() / 1000)
    data1["endDtEpoch"] = Math.floor(new Date(to).getTime() / 1000)
    if($('#searchByUser').val() !== ""){
      data1["viewBy"] = ""
    }else{
    data1["viewBy"] = $('#viewBy').val();
    }

    $.ajax({
        type: 'POST',
        url: '/dateRangeSgErrorsEpoch',
        data: JSON.stringify(data1),
        dataType: 'json',
        contentType:'application/json; charset=utf-8',
        success: function(data2) { 
          addIntoMainChart(data2)
        }
    });


  }

  function addIntoMainChart(data2){

    if(data2 == []){
      return
    }

    var valuesErrorCount = 0
    var queryErrorCount = 0
    var importErrorCount = 0
    var wsErrorCount = 0
    var genErrorCount = 0

    var newDataset =   {
      label: "SG Process Errors",
      backgroundColor: '#5E5E5E',
      borderWidth: 1,
      data:[]
    }


    $.each(data2, function(key, value) {  
        queryErrorCount += value.query;
        importErrorCount += value.import;
        wsErrorCount += value.ws;
        genErrorCount += value.gen;
        
        var tErrors = value.query + value.dcp + value.import + value.sgDb + value.ws + value.gen;
        valuesErrorCount += tErrors;
        var gTime = value.dt;
        newDataset.data.push({x:gTime,y:tErrors})
        });
      
    c1.config.data.datasets.push(newDataset);
    c1.update();

    $('#sgErrorResultSize').html(valuesErrorCount)
    var qPer = (queryErrorCount/valuesErrorCount) * 100
    $("#queryErrorPer").html(qPer.toFixed(1))
    var importPer = (importErrorCount/valuesErrorCount) * 100
    $("#importErrorPer").html(importPer.toFixed(1))
    var wsPer = (wsErrorCount/valuesErrorCount) * 100
    $("#wsErrorPer").html(wsPer.toFixed(1))
    var genPer = (genErrorCount/valuesErrorCount) * 100
    $("#genErrorPer").html(genPer.toFixed(1))
  
  }



  function bigSearch(){

    var from = $('#dtFrom').val();
    var to = $('#dtTo').val();
    if(from ==="" && to === ""){
      $.notify("Pick a Date Range");
      return
    }

    if(sgName === ""){
      $.notify("Pick a SG DB");
      return
    }

    var data1 = {}
    data1["sgDb"] = $('#sgDbListOptions').val()
    data1['startDt'] = from
    data1['endDt'] = to
    data1["startDtEpoch"] = Math.floor(new Date(from).getTime() / 1000)
    data1["endDtEpoch"] = Math.floor(new Date(to).getTime() / 1000)
    data1["user"] = $('#searchByUser').val()
    data1["syncResult"] = $("#syncResult").val();
    data1["changeCount"] = $('#changeCount').val()
    data1["syncTime"] = $('#syncTime').val()
    data1["filterByChannels"] = $('#filterByChannels').is(":checked");
    data1["conflicts"] = $('#conflicts').is(":checked");
    data1["sinceZero"] = $('#sinceZero').is(":checked");
    data1["errors"] = $('#errors').is(":checked");
    data1["noPushes"] = $('#noPushes').val();
    data1["attachments"] = $('#hasAttachments').is(":checked")
    data1["attachmentsPull"] = $('#hasPullAttachments').is(":checked")
    if($('#searchByUser').val() !== ""){
      data1["viewBy"] = ""
    }else{
    data1["viewBy"] = $('#viewBy').val();
    }
    data1['pie'] = false;
 

      $.ajax({
        type: 'POST',
        url: '/dateRangeEpoch',
        data: JSON.stringify(data1),
        dataType: 'json',
        contentType:'application/json; charset=utf-8',
        success: function(data2) { 
          makeChart(data2)
        }
    });

    $.ajax({
        type: 'POST',
        url: '/dtDiffSecStatsEpoch',
        data: JSON.stringify(data1),
        dataType: 'json',
        contentType:'application/json; charset=utf-8',
        success: function(data3) { 
         makeChartDiffSecStat(data3)
        }
    });

}

function bigSearchPie(){

  var from = $('#dtFrom').val();
    var to = $('#dtTo').val();
    if(from ==="" && to === ""){
      $.notify("Pick a Date Range");
      return
    }

    if(sgName === ""){
      $.notify("Pick a SG DB");
      return
    }

    var data1 = {}
    data1["sgDb"] = $('#sgDbListOptions').val()
    data1['startDt'] = from
    data1['endDt'] = to
    data1["startDtEpoch"] = Math.floor(new Date(from).getTime() / 1000)
    data1["endDtEpoch"] = Math.floor(new Date(to).getTime() / 1000)
    data1["user"] = $('#searchByUser').val()
    data1["syncResult"] = $("#syncResult").val();
    data1["changeCount"] = $('#changeCount').val()
    data1["syncTime"] = $('#syncTime').val()
    data1["filterByChannels"] = $('#filterByChannels').is(":checked");
    data1["conflicts"] = $('#conflicts').is(":checked");
    data1["sinceZero"] = $('#sinceZero').is(":checked");
    data1["errors"] = $('#errors').is(":checked");
    data1["noPushes"] = $('#noPushes').val();
    data1["attachments"] = $('#hasAttachments').is(":checked")
    data1["attachmentsPull"] = $('#hasPullAttachments').is(":checked")
    data1["viewBy"] = ""
    data1['pie'] = true;


    $.ajax({
        type: 'POST',
        url: '/dateRangeEpoch',
        data: JSON.stringify(data1),
        dataType: 'json',
        contentType:'application/json; charset=utf-8',
        success: function(data2) {           
           makeChartPie(data2)
        }
    });

}

function  makeChartDiffSecStat(data){

  if(typeof c6 !== 'undefined'){
        c6.destroy(); 
        }

        labelsJ = []
        valuesDiffCount = []
        var ctx6 = document.getElementById('myChart6');

        $.each(data, function(key, value) {  
        valuesDiffCount.push(value.tCount)
        labelsJ.push(value.tRange.substring(4)) 
        });


    c6 = new Chart(ctx6, {
    type: 'bar',
    data: {
      labels: labelsJ,
      datasets: [
      {
        label: 'Sec/Minutes',
        data: valuesDiffCount,
        borderWidth: 2,
        type:'bar',
        borderColor: '#0066ff',
        backgroundColor: '#6699ff'
      }
    ]
    },
    options: {
      plugins: {
        datalabels: { 
                anchor: 'end',
                align: 'top',
                formatter: Math.round,
                font: {
                    weight: 'bold',
                    size: 16
                }
            },
        legend: { display: false }, 
      title: {
        display: true,
        text: 'CBL Connected Times'
      }
    },
      maintainAspectRatio: false,
      scales: {
        y: {

        },
        x: {

        },
        
      }
    }
  });
}


function makeChart(data){

  if(typeof c1 !== 'undefined' || typeof c2 !== 'undefined'){
         c1.destroy(); c2.destroy(); 
        }
   $('#resultSize').html('');
   $('#userSyncStats').empty();
 var ctx1 = document.getElementById('myChart1');
 var ctx2 = document.getElementById('myChart2');

  var valuesChangesCache = [];
  var valuesChangesQuery = [];
  var valuesSyncTime = [];
  var valuesErrors = [];
  var valuesConflicts = [];
  var labelsJ = [];
  var cbwsId = []
  var valuesSent = []
  var valuesChangesSent = []
  var valuesSentVsChangesSent = []
  var valuesPullAttachments = []
  var valuesPushAttCount = []
  var valuesPushCount = []
  var resultShow = 0
  var countNoProblems = 0
  var countErrors = 0
  var countConflicts = 0

  var from = new Date( $("#dtFrom").val());
  var to = new Date( $("#dtTo").val())
  var xMin = Math.floor(new Date(from).getTime());
  var xMax = Math.floor(new Date(to).getTime());

  if($('#searchByUser').val() !== ""){
    makeUserDetails(data)
  }

  $.each(data, function(key, value) {   
    var gTime = value.dt
    resultShow = resultShow + value.dtCount   
    valuesErrors.push({x:gTime,y:value.errors})
    valuesChangesCache.push({x:gTime,y:value.cRow})
    valuesChangesQuery.push({x:gTime,y:value.qRow})
    valuesSyncTime.push({x:gTime,y:value.dtDiffSec})
    valuesConflicts.push({x:gTime,y:value.conflicts})
    valuesSent.push({x:gTime,y:value.sentCount})
    valuesChangesSent.push({x:gTime,y:value.tRow})
    valuesSentVsChangesSent.push({x:gTime,y:value.sent/value.tRow})
    valuesPullAttachments.push({x:gTime,y:value.pullAttCount})
    valuesPushAttCount.push({x:gTime,y:value.pushAttCount})
    valuesPushCount.push({x:gTime,y:value.pushCount})
    labelsJ.push(gTime) 
  });


  c1 = new Chart(ctx1, {
    type: 'line',
    data: {
      labels: labelsJ,
      datasets: [  
      {
        label: '_changes Sent',
        data: valuesChangesSent,
        borderWidth: 1,
        borderColor: '#FFA955',
        backgroundColor: '#FFCFA3'
      },
      {
        label: 'Docs Pulled',
        data: valuesSent,
        borderWidth: 1,
        borderColor: '#36A2EB',
        backgroundColor: '#A0D1F5'
      }, 
      {
        label: 'Docs Pushed',
        data: valuesPushCount,
        borderWidth: 1,
        borderColor: '#9C9C9C',
        backgroundColor: '#CFCFCF'
      },  
      {
        label: 'Attachments: Pushed',
        data: valuesPushAttCount,
        borderWidth: 1,
        borderColor: '#9467B6',
        backgroundColor: '#D093FF'
      },{
        label: 'Attachments: Pulled',
        data: valuesPullAttachments,
        borderWidth: 1,
        borderColor: '#32D1C0',
        backgroundColor: '#39FEE8'
      },
       {
        label: 'Conflicts in Sync',
        data: valuesConflicts,
        borderWidth: 1,
        borderColor: '#C1C661',
        backgroundColor: '#ECF177'
      },
      {
        label: 'Errors In Sync',
        data: valuesErrors,
        borderWidth: 1,
        borderColor: '#FF6384',
        backgroundColor: '#FFB2C1'
      }
    ]
    },
    options: {
              onClick: (evt, elements, chart) => {
                if (elements[0]) {            
                    const i = elements[0].index;
                    console.log(chart.data.labels[i] + ': ' + chart.data.datasets[0].data[i]);
                  }
                },

      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          type: 'logarithmic'
        }, 
        x :{
          type: 'time',
        }
      },plugins: {
     
        zoom: {
          pan:{
                enabled: true,
                mode: 'x'
              },
            zoom: {
              mode: 'x',
              drag: {
                  enabled: true,
                  backgroundColor: "#E1E1E1", 
                  borderColor: "#AFADAD",
                  borderWidth: 1,
                  modifierKey: 'shift'
              }
            }
          }
        
        }  
    }
  });


  c2 = new Chart(ctx2, {
    type: 'bar',
    data: {
      labels: labelsJ,
      datasets: [
      {
        label: '_changes (Cache Hit)',
        data: valuesChangesCache,
        borderWidth: 1,
        type:'bar',
        borderColor: '#00CF9B',
        backgroundColor: '#00CF9B'
      },
      {
        label: '_changes (SQL++ Query)',
        data: valuesChangesQuery,
        borderWidth: 1,
        type: 'bar',
        borderColor: '#cc33ff',
        backgroundColor: '#cc33ff'
      }
    ]
    },
    options: {
      plugins: {

        zoom: {
          pan:{
                enabled: true,
                mode: 'x'
              },
            zoom: {
              mode: 'x',
              drag: {
                  enabled: true,
                  backgroundColor: "#DADADA", 
                  borderColor: "#AFADAD",
                  borderWidth: 2,
                  modifierKey: 'shift'
              }
            }
          }
      },
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          stacked: true
        },
        x: {
          stacked: true,
          type: 'time'
        }
      }
    }
  });


      $('#resultSize').html(resultShow.toLocaleString());
      sgErrorGraph()

    }

function makeChartPie(data){

if(typeof c3 !== 'undefined'|| typeof c4 !== 'undefined' || typeof c5 !== 'undefined' ){
       c3.destroy(); c4.destroy(); c5.destroy();
      }

var ctx3 = document.getElementById('myChart3');
var ctx4 = document.getElementById('myChart4');
var ctx5 = document.getElementById('myChart5');

var userSyncAllTrue = 0
var userSyncAllFalse = 0
var sinceZeroTrue = 0
var sinceZeroFalse = 0
var channelCache = 0
var channelQuery = 0


var tFrom = new Date( $("#dtFrom").val());
var xAxisStart = Math.floor(tFrom.getTime() / 1000);

var tTo= new Date( $("#dtTo").val())
var xAxisEnd =  Math.floor(tTo.getTime() / 1000);


$.each(data, function(key, value) {   

    if(typeof value.cRow !== 'undefined'){
      channelCache = channelCache + value.cRow
    } 

    if(typeof value.qRow !== 'undefined'){
    channelQuery = channelQuery + value.qRow  
    } 

    if(value.tRow == value.sentCount){
      userSyncAllTrue = userSyncAllTrue + 1
    }else{
      userSyncAllFalse = userSyncAllFalse + 1
    }

    if( value.since == '0' || value.since == 0){
      sinceZeroTrue =  sinceZeroTrue + 1
    } else{
      sinceZeroFalse =  sinceZeroFalse + 1
    }
});



const optionsPie1 = {
  tooltips:{
                enabled: true
              },
  responsive: true,
 maintainAspectRatio: false,
  plugins: { 
     title: {
             display: true,
            text: '_changes Sent VS Docs Pulled'
            },
    legend: {
      position: 'top'
    },
    datalabels: {
      display: 'auto',
      color: 'black',
      font: {
        weight: 'bold'
      },
      formatter: (value, ctx3) => {
        const total = ctx3.chart.getDatasetMeta(0).total;
        let percentage = (value * 100 / total).toFixed(1) + "%";
        return percentage + ' (' + value + ')';
      },
    }
  }
}


c3 = new Chart(ctx3, {
  type: 'pie',
  data: {
    labels: ['Docs Pulled',"Missing or Zero Docs"],
    datasets: [
              {
                data:[userSyncAllTrue,userSyncAllFalse],
                backgroundColor: [
                                  '#00CF9B',
                                  '#E55B5E'
                                  ]
              }
              ]
  },
  options: optionsPie1,
  plugins:[ChartDataLabels]
    });

  const optionsPie2 = {
  tooltips:{
                enabled: true
              },
  responsive: true,
 maintainAspectRatio: false,
  plugins: { 
     title: {
             display: true,
            text: 'Start from Zero (new) VS Old Sync'
            },
    legend: {
      position: 'top'
    },
    datalabels: {
      display: 'auto',
      color: 'black',
      font: {
        weight: 'bold'
      },
      formatter: (value, ctx4) => {
        const total = ctx4.chart.getDatasetMeta(0).total;
        let percentage = (value * 100 / total).toFixed(1) + "%";
        return percentage + ' (' + value + ')';
      },
    }
  }
}

    c4 = new Chart(ctx4, {
  type: 'pie',
  data: {
    labels: ["New Sync (since=0)","Old Sync"],
    datasets: [
                {
                  data:[sinceZeroTrue,sinceZeroFalse],
                  backgroundColor: [
                                    '#3366ff',
                                    '#ff9900'
                                    ]
                }
              ]
  },
  options: optionsPie2,
  plugins:[ChartDataLabels]
    });



  const optionsPie3 = {
  tooltips:{
                enabled: true
              },
  responsive: true,
 maintainAspectRatio: false,
  plugins: { 
     title: {
             display: true,
            text: '_changes: Cache Hit VS SQL++ Query'
            },
    legend: {
      position: 'top'
    },
    datalabels: {
      display: 'auto',
      color: 'black',
      font: {
        weight: 'bold'
      },
      formatter: (value, ctx5) => {
        const total = ctx5.chart.getDatasetMeta(0).total;
        let percentage = (value * 100 / total).toFixed(1) + "%";
        return percentage;
      },
    }
  }
}


    c5 = new Chart(ctx5, {
  type: 'pie',
  data: {
    labels: ["Cache Hit","SQL++ Query"],
    datasets: [
                {
                  data:[channelCache,channelQuery],
                  backgroundColor: [
                                    '#00CF9B',
                                    '#cc33ff'
                                    ]
                }
              ]
  },
  options: optionsPie3,
  plugins:[ChartDataLabels]
    });

 
  }


  function makeUserDetails(data){
    $('#userSyncStats').empty();
    $("#userSyncStatsTable  tbody").empty();

    //$.notify('graph x-axis view by: "All Entries" when user search',"info");

      $.each(data, function(key, value) {  

          var row = '<tr class="text-center-row">'
          row = row + "<td>" +value.dtClock+"</td>"
          row = row + "<td>"+value.cbKey+ "</td>" 
          row = row + "<td>"+value.dtDiffSec +"</td>"

          var r = "";
          if (value.tRow > 0){
          r = (value.cRow/value.tRow) * 100;
          var r = r.toFixed(1);
          }

          row = row + '<td>' + r + '</td>';

          row = row + "<td>" + value.tRow.toLocaleString() + "</td>"

          if(value.tRow === value.sentCount){
            row = row + '<td>' +value.sentCount.toLocaleString()+'</td>'
          }else{
            row = row + '<td><span style="color: orange;">' +value.sentCount.toLocaleString()+'</span></td>';
          }
          row = row + "<td>"+ value.pushCount.toLocaleString() +"</td>"


          if(value.blipC === true){
          row = row + '<td><span style="color: green;">Yes</span></td>';
          }else{
          row = row + '<td><span style="color: orange;">No</span></td>';
          }



          if(value.conflicts > 0){
            row = row + '<td><span style="color: orange;">' +value.conflicts+"</span></td>";
          }else{
            row = row + '<td>' +value.conflicts + '</td>'
          }

          if(value.errors > 0){
            row = row + '<td><span style="color: red;">' +value.errors+"</span></td>";
          }else{
            row = row + '<td>' +value.errors + '</td>'
          }
          row = row + "</tr>"

        $("#userSyncStatsTable tbody").append(row);

        $('#wsDetails').empty();
    

       });
  }
  


function userSyncDetails(wsId){

  $('#wsDetails').empty();
  

  data1 = {'wsId':wsId}

  $.ajax({
    type: 'POST',
    url: '/wsId',
    data: JSON.stringify(data1),
    dataType: 'json',
    contentType:'application/json; charset=utf-8',
    success: function(data2) { 
          var html = ''
          html = html + ' <b>Connection Start:</b> '+ data2['dt']+' <b>End:</b> ' + data2["dtEnd"] + ' <b>Connection Time(sec):</b> '+ data2['dtDiffSec']+'</br>'
          html = html + '  <b>Filtered By Channel(s):</b> ' + data2["filterBy"] + ' </br>'
          html = html + '  <b>Since:</b> ' + data2["since"] + ' </br>'
          html = html + wsIdMakeHtml(data2["log"])
          $('#wsDetails').html(html)
        }
    });
  }


function wsIdMakeHtml(data){
  var html = '<b>Raw Sync Log</b> </br>'
  $.each(data, function(key, value) {

    var value = value.replace(/(error|Error)/g, '<mark>$1</mark>');

    var c = "dark"
    if(key % 2 == 0) {
      c = "light"
      }
    html = html + '<div class="ws-'+c+'" >'+ value + '</div>'
    });
  return html
}

function getSampleDt(){

  $.ajax({
        url: "/lastWsIdEpoch",
        type: 'GET',
        dataType: 'json', // added data type
        success: function(data) {

          if (data.length > 0){
          $('#dtFrom').val(data[0]['dtHrAgo']);
          $('#dtTo').val(data[0]['dt']);
          sgDbListGet();
          }else{
            $.notify("No CBL WebSocket Connections");
          }

        }
    });
}

function userFill(username){
  $("#viewBy").prop("disabled", false);
  $('#searchByUser').val(username);
}

 function closeUserDetails(divId){
   $("#wsIdDetails-"+divId).hide();
 }

 function openUserDetails(divId){
   $("#wsIdDetails-"+divId).show();
 }

 $('.zoomReset').click(function(){
    c1.resetZoom();
    c2.resetZoom();
});

$("#search").click(function(e){
    sgUserList();
    bigSearch();
    bigSearchPie();
  });