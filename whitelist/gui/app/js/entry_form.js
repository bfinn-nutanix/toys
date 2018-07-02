$(document).ready(function(){
  function populateForm(checksum) {
    $.get("../../../api/entries", {"checksum": checksum},
      function(response, status, xhr) {
        hypervisor = response["hypervisor"]
        $("#checksum").val(checksum);
        $("#version").val(response["version"]);
        $("#friendly_name").val(response["friendly_name"]);
        $("#hypervisor").val(hypervisor);
        $("#min_nos").val(response["min_nos"]);
        $("#min_foundation").val(response["min_foundation"]);
        // TODO: Only respects one version for now.
        // TODO: literal string print
        compatible_versions = response["compatible_versions"][hypervisor];
        $("#compatible_versions").val(JSON.stringify(compatible_versions[0]));
        $("#unsupported_hardware").val(
          JSON.stringify(response["unsupported_hardware"][0]));
        $("#deprecated_version").val(response["deprecated"]);
        $("#skus").val(response["skus"]);
        $("#validated").prop("checked", response["validated"]);
      });
  };

  function parseChecksumFromUrl(){
    parts = window.location.href.split("?");
    if (parts.length == 1) {
      return null;
    } else if (parts.length != 2) {
      console.log(`URL ${window.location.href} should only have one \"?\"`);
      return null;
    }
    params = parts[1].split("&");
    for (i=0; i < params.length; i++) {
      param = params[i].split("=");
      if (param[0] == "checksum") {
        return param[1];
      }
    };
  };

  function submitForm(){
    checksum = $("#checksum").val();
    hypervisor = $("#hypervisor").val();
    entry = {
      "min_foundation": $("#min_foundation").val(),
      "hypervisor": hypervisor,
      "min_nos": $("#min_nos").val(),
      "friendly_name": $("#friendly_name").val(),
      "version": $("#version").val(),
      "unsupported_hardware": $("#unsupported_hardware").val() ?
        [$("#unsupported_hardware").val().split(",")] : [],
      "compatible_versions": {
        [hypervisor]: $("#min_nos").val() ? [$("#min_nos").val()] : []
      },
      "skus": $("#skus").val(),
      "validated": $("#validated").prop("checked")
    };
    console.log(`Checksum: ${checksum}`);
    console.log(`Body: ${JSON.stringify(entry, null, 2)}`);

    // If the page was loaded with a checksum, we should PUT rather than POST.
    is_update = Boolean(parseChecksumFromUrl());
    $.ajax({
      "url": `../../../api/entries?checksum=${checksum}`,
      "method": is_update ? "PUT" : "POST",
      "contentType": "application/json",
      "data": JSON.stringify(entry),
      "processData": false,
      "success": function(data, textStatus, jqXHR) {
        console.log("yay!");
        window.location = "entry_list.html";
      },
      "error": function(data, textStatus, jqXHR) {
        console.error(`Failure: ${textStatus}\n${JSON.stringify(data, null, 2)}`);
      }
    });
  };

  $("#submit").click(submitForm);

  checksum = parseChecksumFromUrl();
  if (checksum) {
    populateForm(checksum);
  }
});
