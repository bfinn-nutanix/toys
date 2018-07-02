$(document).ready(function(){
  function populateTable() {
    $.get("../../../api/entries", {}, function(response, status, xhr) {
      console.log(response);
      $("#entry_table tbody > tr").remove();
      $.each(response, function(index, checksum) {
        $.get("../../../api/entries", {"checksum": checksum},
          function(response, status, xhr) {
            var row = "";
            row = row + "<td>" + checksum + "</td>";
            row = row + "<td>" + response["friendly_name"] + "</td>";
            row = row + "<td>" + Boolean(response["validated"]) + "</td>";
            row = row + "<td><a href=\"entry_form.html?checksum=" +
              checksum + "\">Edit</a></td>";
            $("#entry_table tbody").append(
              "<tr>" + row + "</tr>");
          });
        });
      });
    };

  $("#refresh").bind("click", populateTable);
  $("#push").bind("click", function(){
    $.get("../../../api/file/push_validated_whitelist_to_gerrit", {},
      function(response, status, xhr) {
        $("#gerrit_text").text(response);
        $("#gerrit_modal").modal();
      });
  });

  // Initialize the page.
  populateTable();
});
