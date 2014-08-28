// Generated by CoffeeScript 1.6.3
/* Contains a list of currently selected DT_RowId (info_hash's)*/


(function() {
  var action_reannounce, action_recheck, action_remove, action_remove_data, action_start, action_stop, action_torrent_details, action_torrent_peers, action_torrent_speed, bytes_to_size, chart_update, client_chart, detail_elements, detail_traffic_chart, detail_update_speed, detail_update_timer, endpoint, fmt_duration, fmt_timestamp, graph_fps, graph_type, graph_window_size, handle_event_alert, handle_event_speed_overall_response, handle_event_torrent_details_response, handle_event_torrent_files_response, handle_event_torrent_list_response, handle_event_torrent_peers_response, handle_event_torrent_reannounce_response, handle_event_torrent_recheck_response, handle_event_torrent_remove_response, handle_event_torrent_speed_response, handle_event_torrent_stop_response, has_connected, in_url, overall_speed_update, overall_speed_update_timer, peer_chart, peer_update_timer, queue_size, render_peers, row_load_handler, row_remove, row_select_handler, selected_class, selected_detail_id, selected_rows, show_alert, socket, speed_dn, speed_up, speed_update_timer, torrent_table, ts, update_speed, user_messages, _alert_num, _sizes;

  selected_rows = [];

  /* class defining selected rows in the torrent listing*/


  selected_class = 'selected';

  /* Currently selected torrent that should be used in the detail display*/


  selected_detail_id = false;

  /* Application endpoint prefix*/


  endpoint = "http://" + document.domain + ":" + location.port + "/ws";

  /* Update interval for the traffic graph in ms*/


  update_speed = 1000;

  /* Type of graph to draw. time.area is an alternate*/


  graph_type = 'time.line';

  /* Number of frames per second that transitions animations should use.*/


  graph_fps = 60;

  /* Number of entries to keep in working memory while the chart is not animating transitions.*/


  queue_size = 240;

  /* Number of entries to display in the graph.*/


  graph_window_size = 60;

  /* Update interval for the stats/detail tabs*/


  detail_update_speed = update_speed * 2;

  /* Timer to update the selected torrent detail page*/


  detail_update_timer = null;

  /* Timer for the overall speed indicator*/


  overall_speed_update_timer = null;

  /* Timer to update the selected torrent speed graph*/


  speed_update_timer = null;

  /* Timer to update the selected torrent peer list*/


  peer_update_timer = null;

  /* socket.io-client instance*/


  socket = null;

  /* Keep track of if we have connected before or not*/


  has_connected = false;

  /* Element used to show flash message*/


  user_messages = jQuery("#user_messages");

  /* Overall speed indicator elements*/


  speed_up = jQuery("#speed_up");

  speed_dn = jQuery("#speed_dn");

  torrent_table = jQuery('#torrent_table').dataTable({
    processing: true,
    serverSize: true,
    paginate: false,
    searching: false,
    autoWidth: true,
    sDom: 'Rlfrtip',
    scrollY: 300,
    columns: [
      {
        data: 'name'
      }, {
        data: 'size'
      }, {
        data: 'progress'
      }, {
        data: 'ratio'
      }, {
        data: 'up_rate'
      }, {
        data: 'dn_rate'
      }, {
        data: 'leechers'
      }, {
        data: 'peers'
      }, {
        data: 'priority'
      }, {
        data: 'is_active'
      }
    ],
    rowCallback: row_load_handler,
    columnDefs: [
      {
        render: function(data, type, row) {
          var pct, style;
          pct = Math.floor(data);
          style = pct >= 100 ? "success" : "alert";
          return "<div class=\"progress " + style + "\">\n    <span style=\"float: left\">" + data + "%</span>\n    <span class=\"meter\" style=\"width: " + data + "\"></span>\n</div>";
        },
        targets: 2
      }, {
        render: function(data, type, row) {
          var class_name;
          class_name = data < 1 ? 'alert' : 'success';
          return "<span class=\"" + class_name + "\">" + data + "</span>";
        },
        targets: 3
      }
    ]
  });

  /* Initialize epoch chart on the traffic tab*/


  detail_traffic_chart = jQuery('#detail-traffic-chart').epoch({
    type: graph_type,
    data: [
      {
        label: "upload",
        values: []
      }, {
        label: "download",
        values: []
      }
    ],
    axes: ['left', 'right'],
    fps: graph_fps,
    windowSize: graph_window_size,
    queueSize: queue_size
  });

  /* Initialize peer chart on the peers tab*/


  peer_chart = jQuery("#peer_chart").epoch({
    type: 'pie',
    inner: 50
  });

  client_chart = jQuery("#client_chart").epoch({
    type: 'pie',
    inner: 50
  });

  /*
      Called for each new row loaded into the data table
  
      @param {string} DT_RowId defined for the row ( which corresponds to the info_hash )
      @param {object} The rows data object
      @param {number} Index of the row in the table
  */


  row_load_handler = function(row, data, displayIndex) {
    if (jQuery.inArray(data.DT_RowId, selected_rows) !== -1) {
      return jQuery(row).addClass(selected_class);
    }
  };

  /*
      Called when a user selects a row with the cursor. Will update the currently selected rows.
      If the user holds ctrl while clicking the row will be added to the selected_rows array. Otherwise
      the row will be "activated" and show more detailed information for that row in another panel.
  */


  row_select_handler = function(e) {
    var existing_row_id, index, row_id, _i, _len;
    row_id = this.id;
    if (e.ctrlKey) {
      index = _.indexOf(selected_rows, row_id);
      if (index === -1) {
        selected_rows.push(row_id);
      } else {
        selected_rows.splice(index, 1);
      }
      return jQuery(this).toggleClass(selected_class);
    } else {
      for (_i = 0, _len = selected_rows.length; _i < _len; _i++) {
        existing_row_id = selected_rows[_i];
        jQuery("#" + existing_row_id).removeClass(selected_class);
      }
      selected_rows = [row_id];
      selected_detail_id = row_id;
      if (detail_update_timer !== null) {
        clearTimeout(detail_update_timer);
      }
      if (speed_update_timer !== null) {
        clearTimeout(speed_update_timer);
      }
      if (peer_update_timer !== null) {
        clearTimeout(peer_update_timer);
      }
      action_torrent_details();
      action_torrent_speed();
      action_torrent_peers();
      return jQuery("#" + row_id).addClass(selected_class);
    }
  };

  /*
  Remove a row from the torrent list by its info_hash
  */


  row_remove = function(info_hash) {
    return jQuery("#" + info_hash).remove();
  };

  /* Client actions*/


  action_recheck = function() {
    if (selected_rows) {
      socket.emit('event_torrent_recheck', {
        info_hash: selected_rows
      });
      return false;
    }
  };

  action_reannounce = function() {
    if (selected_rows) {
      return socket.emit('event_torrent_announce', {
        info_hash: selected_rows
      });
    }
  };

  action_remove = function() {
    var info_hash, _i, _len, _results;
    _results = [];
    for (_i = 0, _len = selected_rows.length; _i < _len; _i++) {
      info_hash = selected_rows[_i];
      _results.push(socket.emit('event_torrent_remove', {
        info_hash: info_hash,
        remove_data: false
      }));
    }
    return _results;
  };

  action_remove_data = function() {
    var info_hash, _i, _len, _results;
    _results = [];
    for (_i = 0, _len = selected_rows.length; _i < _len; _i++) {
      info_hash = selected_rows[_i];
      _results.push(socket.emit('event_torrent_remove', {
        info_hash: info_hash,
        remove_data: true
      }));
    }
    return _results;
  };

  action_stop = function() {
    if (selected_rows) {
      return socket.emit('event_torrent_stop', {
        info_hash: selected_rows
      });
    }
  };

  action_start = function() {
    if (selected_rows) {
      return socket.emit('event_torrent_start', {
        info_hash: selected_rows
      });
    }
  };

  action_torrent_details = function() {
    if (selected_detail_id) {
      return socket.emit('event_torrent_details', {
        info_hash: selected_detail_id
      });
    }
  };

  action_torrent_speed = function() {
    if (selected_detail_id) {
      socket.emit('event_torrent_speed', {
        info_hash: selected_detail_id
      });
    }
    return speed_update_timer = setTimeout(action_torrent_speed, update_speed);
  };

  action_torrent_peers = function() {
    if (selected_detail_id) {
      socket.emit('event_torrent_peers', {
        info_hash: selected_detail_id
      });
    }
    return peer_update_timer = setTimeout(action_torrent_peers, update_speed);
  };

  /*
      Response handlers for sent websocket events
  */


  handle_event_torrent_files_response = function(message) {
    return false;
  };

  handle_event_torrent_reannounce_response = function(message) {
    return show_alert("Got reannounce response");
  };

  handle_event_torrent_recheck_response = function(message) {
    return show_alert("Got recheck response");
  };

  handle_event_alert = function(message) {
    return show_alert(message['msg'], message['msg_type']);
  };

  handle_event_torrent_list_response = function(message) {
    var row, _i, _len, _ref, _results;
    _ref = message['data'];
    _results = [];
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      row = _ref[_i];
      _results.push(torrent_table.fnAddData(row));
    }
    return _results;
  };

  handle_event_torrent_stop_response = function(message) {
    return show_alert(message['msg'], message['msg_type']);
  };

  handle_event_speed_overall_response = function(message) {
    speed_up.text(bytes_to_size(message['data']['up'], true));
    return speed_dn.text(bytes_to_size(message['data']['dn'], true));
  };

  handle_event_torrent_speed_response = function(message) {
    return chart_update(message['data']['download_payload_rate'], message['data']['upload_payload_rate']);
  };

  handle_event_torrent_peers_response = function(message) {
    var client, client_chart_data, count, country, peer_chart_data, sort_client, _ref, _ref1;
    sort_client = function(peer) {
      return (peer['client'].split(" ")).slice(0, -1).toString();
    };
    peer_chart_data = [];
    client_chart_data = [];
    _ref = _.countBy(message['data']['peers'], 'country');
    for (country in _ref) {
      count = _ref[country];
      peer_chart_data.push({
        label: country,
        value: count
      });
    }
    _ref1 = _.countBy(message['data']['peers'], sort_client);
    for (client in _ref1) {
      count = _ref1[client];
      client_chart_data.push({
        label: client,
        value: count
      });
    }
    peer_chart.update(peer_chart_data);
    client_chart.update(client_chart_data);
    return render_peers(message['data']['peers']);
  };

  handle_event_torrent_remove_response = function(message) {
    if (message['status'] === 0) {
      return jQuery("#" + message['data']['info_hash']).remove();
    }
  };

  handle_event_torrent_details_response = function(message) {
    var data, eta, peers, pieces, seeds;
    data = message['data'];
    eta = data['eta'] === 0 ? '∞' : fmt_duration(data['eta']);
    seeds = "" + data['num_seeds'] + " (" + data['total_seeds'] + ")";
    peers = "" + data['num_peers'] + " (" + data['total_peers'] + ")";
    pieces = "" + data['num_pieces'] + " (" + data['piece_length'] + ")";
    detail_elements.detail_downloaded.text(bytes_to_size(data['total_done']));
    detail_elements.detail_uploaded.text(bytes_to_size(data['total_uploaded']));
    detail_elements.detail_tracker_status.text(data['tracker_status']);
    detail_elements.detail_ratio.text(data['ratio'].toFixed(2));
    detail_elements.detail_next_announce.text(data['next_announce']);
    detail_elements.detail_speed_dl.text(bytes_to_size(data['download_payload_rate'], true));
    detail_elements.detail_speed_ul.text(bytes_to_size(data['upload_payload_rate'], true));
    detail_elements.detail_eta.text(eta);
    detail_elements.detail_pieces.text(pieces);
    detail_elements.detail_seeders.text(seeds);
    detail_elements.detail_peers.text(peers);
    detail_elements.detail_availability.text(data['distributed_copies']);
    detail_elements.detail_active_time.text(fmt_duration(data['active_time']));
    detail_elements.detail_seeding_time.text(fmt_duration(data['seeding_time']));
    detail_elements.detail_added_on.text(fmt_timestamp(data['time_added']));
    detail_elements.detail_name.text(data['name']);
    detail_elements.detail_hash.text(selected_detail_id);
    detail_elements.detail_path.text(data['save_path']);
    detail_elements.detail_total_size.text(data['total_size']);
    detail_elements.detail_num_files.text(data['detail_num_files']);
    detail_elements.detail_status.text(data['detail_status']);
    return detail_elements.detail_tracker.text(data['tracker_host']);
  };

  /*
      Show an alert popup message to the user. The message will fade after a few seconds have passed
  
      @param {string} Message to display
      @param {string} Type of message (css class used)
      @param {number} Time in seconds to show the message
  */


  show_alert = function(msg, msg_type, ttl) {
    if (msg_type == null) {
      msg_type = 'info';
    }
    if (ttl == null) {
      ttl = 5;
    }
    _alert_num += 1;
    user_messages.append("<div id=\"alert_" + _alert_num + "\" data-alert class=\"alert-box radius " + msg_type + "\">" + msg + "<a href=\"#\" class=\"close\">&times;</a></div>");
    if (ttl > 0) {
      return setTimeout((function() {
        return jQuery("#alert_" + _alert_num).fadeOut(function() {
          return this.remove();
        });
      }), ttl * 1000);
    }
  };

  _alert_num = 0;

  /* Update the chart values with the latest speed values*/


  chart_update = function(upload, download) {
    var update_data;
    update_data = [
      {
        time: ts(),
        y: upload
      }, {
        time: ts(),
        y: download
      }
    ];
    return detail_traffic_chart.push(update_data);
  };

  fmt_timestamp = function(ts) {
    return moment.unix(ts).format('D/M/YYYY hh:mm:s');
  };

  fmt_duration = function(seconds) {
    return moment.duration(seconds, 'seconds').humanize();
  };

  overall_speed_update = function() {
    socket.emit('event_speed_overall', {});
    return overall_speed_update_timer = setTimeout(overall_speed_update, update_speed);
  };

  _sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

  bytes_to_size = function(bytes, per_sec) {
    var human_size, i, k;
    if (per_sec == null) {
      per_sec = false;
    }
    if (bytes <= 1000) {
      if (per_sec) {
        return "" + bytes + " B/s";
      } else {
        return "" + bytes + " B";
      }
    }
    k = 1000;
    i = Math.floor(Math.log(bytes) / Math.log(k));
    human_size = (bytes / Math.pow(k, i)).toPrecision(2) + ' ' + _sizes[i];
    if (per_sec) {
      human_size = "" + human_size + "/s";
    }
    return human_size;
  };

  render_peers = function(peer_list) {
    var output_html, peer, _i, _len;
    output_html = [];
    for (_i = 0, _len = peer_list.length; _i < _len; _i++) {
      peer = peer_list[_i];
      output_html.push("<tr>\n    <td><img src=\"/static/img/country/" + (peer['country'].toLowerCase()) + ".png\"></td>\n    <td>" + peer['ip'] + "</td>\n    <td>" + peer['client'] + "</td>\n    <td><div class=\"progress\"><span class=\"meter\" style=\"" + (peer['progress'] * 100) + "\"></span></div></td>\n    <td>" + (bytes_to_size(peer['down_speed'], true)) + "</td>\n    <td>" + (bytes_to_size(peer['up_speed'], true)) + "</td>\n</tr>");
    }
    return jQuery("#peer_list tbody").html(output_html.join(""));
  };

  /* Return the current unix timestamp in seconds*/


  ts = function() {
    return Math.round(new Date().getTime() / 1000) | 0;
  };

  /* Cache all the detail element nodes*/


  detail_elements = {
    detail_downloaded: jQuery("#detail_downloaded"),
    detail_uploaded: jQuery("#detail_uploaded"),
    detail_ratio: jQuery("#detail_ratio"),
    detail_next_announce: jQuery("#detail_next_announce"),
    detail_tracker_status: jQuery("#detail_tracker_status"),
    detail_speed_dl: jQuery("#detail_speed_dl"),
    detail_speed_ul: jQuery("#detail_speed_ul"),
    detail_eta: jQuery("#detail_eta"),
    detail_pieces: jQuery("#detail_pieces"),
    detail_seeders: jQuery("#detail_seeders"),
    detail_peers: jQuery("#detail_peers"),
    detail_availability: jQuery("#detail_availability"),
    detail_active_time: jQuery("#detail_active_time"),
    detail_seeding_time: jQuery("#detail_seeding_time"),
    detail_added_on: jQuery("#detail_added_on"),
    detail_name: jQuery("#detail_name"),
    detail_hash: jQuery("#detail_hash"),
    detail_path: jQuery("#detail_path"),
    detail_total_size: jQuery("#detail_total_size"),
    detail_num_files: jQuery("#detail_num_files"),
    detail_comment: jQuery("#detail_comment"),
    detail_status: jQuery("#detail_status"),
    detail_tracker: jQuery("#detail_tracker")
  };

  /* Check for the existence of a string in the URL*/


  in_url = function(text) {
    return window.location.pathname.indexOf(text) !== -1;
  };

  jQuery(function() {
    socket = io.connect(endpoint);
    socket.on('connect', function() {
      var e;
      if (has_connected) {
        show_alert("Reconnected to backend successfully");
      } else {
        show_alert("Connected to backend successfully");
      }
      if (in_url("/torrents/")) {
        try {
          torrent_table.fnClearTable();
        } catch (_error) {
          e = _error;
          null;
        }
        socket.emit('event_torrent_list');
      }
      overall_speed_update();
      return has_connected = true;
    });
    socket.on('event_speed_overall_response', handle_event_speed_overall_response);
    if (in_url("/torrents/")) {
      socket.on('event_torrent_recheck', handle_event_torrent_recheck_response);
      socket.on('event_torrent_peers_response', handle_event_torrent_peers_response);
      socket.on('event_torrent_speed_response', handle_event_torrent_speed_response);
      socket.on('event_torrent_details_response', handle_event_torrent_details_response);
      socket.on('event_torrent_files', handle_event_torrent_files_response);
      socket.on('event_torrent_list_response', handle_event_torrent_list_response);
      socket.on('event_torrent_remove_response', handle_event_torrent_remove_response);
      socket.on('event_alert', handle_event_alert);
      socket.on('event_torrent_reannounce_response', handle_event_torrent_reannounce_response);
      socket.on('event_torrent_stop_response', handle_event_torrent_stop_response);
      jQuery('#torrent_table tbody').on('click', 'tr', row_select_handler);
      jQuery('#action_stop').on('click', action_stop);
      jQuery('#action_start').on('click', action_start);
      jQuery('#action_recheck').on('click', action_recheck);
      jQuery('#action_reannounce').on('click', action_reannounce);
      jQuery('#action_remove').on('click', action_remove);
      jQuery('#action_remove_data').on('click', action_remove_data);
      return jQuery('#resize_columns').on('click', function() {
        return torrent_table.fnAdjustColumnSizing(true);
      });
    }
  });

}).call(this);

/*
//@ sourceMappingURL=tranny-torrents.map
*/
