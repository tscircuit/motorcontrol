// The dashboards need Web Serial. Say so up front where it is missing,
// for example after scanning the booklet's QR code with a phone.
(() => {
  if ("serial" in navigator) return;
  const note = document.getElementById("browserNote");
  note.classList.add("unsupported");
  note.textContent = "This browser can’t connect to USB devices. To control your motor, open motorcontrol.tscircuit.com in Chrome or Edge on a desktop or laptop.";
})();
