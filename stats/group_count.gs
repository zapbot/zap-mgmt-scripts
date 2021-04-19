// A Google Apps Script for counting the number of messages and threads from the ZAP User Group in a Gmail account
// For more details see https://www.zaproxy.org/blog/2021-04-19-collecting-statistics-for-open-source-projects/

function user_group_count_by_month() {
  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = spreadsheet.getSheetByName('User Group');
  //sheet.clear();
  //sheet.appendRow(['Date', 'Group', 'Count', 'Threads', 'Query']);
  for (var year=2021; year < 2022; year++) {
    for (var mon=1; mon < 13; mon++) {
      var total = 0;
      var q = "subject:zaproxy-users after:" + get_date_start_str(year, mon) + " before:" + get_date_end_str(year, mon)
      var inbox_threads = GmailApp.search(q);
      for (var i = 0; i < inbox_threads.length; i++) {
        var message = inbox_threads[i].getMessages();
        for (var x = 0; x < message.length; x++) {
          total += 1;
        }
      }
      sheet.appendRow([get_date_start_str(year, mon), 'zaproxy-users', total, inbox_threads.length, q]);
    }
  }
}

function two(c) {
  if (c < 10) {
    return "0" + c;
  }
  return "" + c;
}

function get_date_start_str(year, mon) {
  return year + "/" + two(mon) + "/01";
}

function get_date_end_str(year, mon) {
  if (mon == 12) {
    return year + 1 + "/01/01";
  }
  return year + "/" + two(mon+1) + "/01";
}
