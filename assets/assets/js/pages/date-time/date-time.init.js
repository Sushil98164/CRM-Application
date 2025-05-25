$(document).ready(function () {
  flatpickr("#date", {
    dateFormat: "Y-m-d",
    allowInput: true,
    onOpen: function (selectedDates, dateStr, instance) {
      instance.setDate(instance.input.value, false);
    },
  });
  flatpickr(".DateTimeNew", {
    dateFormat: "Y-m-d",
    allowInput: true,
    onOpen: function (selectedDates, dateStr, instance) {
      instance.setDate(instance.input.value, false);
    },
  });
  flatpickr("#date1", {
    dateFormat: "Y-m-d",
    allowInput: true,
    onOpen: function (selectedDates, dateStr, instance) {
      instance.setDate(instance.input.value, false);
    },
  });

  flatpickr("#datetime", {
    enableTime: true,
    dateFormat: "Y-m-d H:i",
    onOpen: function (selectedDates, dateStr, instance) {
      instance.setDate(instance.input.value, false);
    },
  });

  flatpickr("#dateOfBirth", {
    dateFormat: "Y-m-d",
    allowInput: true,
    onOpen: function (selectedDates, dateStr, instance) {
      instance.setDate(instance.input.value, false);
    },
  });

  flatpickr("#therapyDate", {
    dateFormat: "Y-m-d",
    allowInput: true,
    onOpen: function (selectedDates, dateStr, instance) {
      instance.setDate(instance.input.value, false);
    },
  });

  if (document.getElementById("dateIcon")) {
    const nativeElement = document.getElementById("dateIcon");

    flatpickr(nativeElement, {
      dateFormat: "Y-m-d",
      allowInput: true,
      wrap: true,
    });
  }

  if (document.getElementById("dateIcon2")) {
    const nativeElement = document.getElementById("dateIcon2");

    flatpickr(nativeElement, {
      dateFormat: "Y-m-d",
      allowInput: true,
      wrap: true,
    });
  }

  flatpickr("#time", {
    enableTime: true,
    noCalendar: true,
    dateFormat: "H:i",
    onOpen: function (selectedDates, dateStr, instance) {
      instance.setDate(instance.input.value, false);
    },
  });
  flatpickr("#multiselectdate", {
    mode: "multiple",
    dateFormat: "Y-m-d",
    onOpen: function (selectedDates, dateStr, instance) {
      instance.setDate(instance.input.value, false);
    },
  });
  flatpickr("#daterange", {
    mode: "range",
    onOpen: function (selectedDates, dateStr, instance) {
      instance.setDate(instance.input.value, false);
    },
  });
});
