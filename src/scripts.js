document.addEventListener('DOMContentLoaded', () => {
  const mapBox = document.getElementById('mapSection');
  const optionBox = document.getElementById('optionSection');
  const summaryBox = document.getElementById('summarySection');

  mapBox.addEventListener('click', () => {
    console.log('Map panel clicked');
  });

  optionBox.addEventListener('click', () => {
    console.log('Option panel clicked');
  });

  summaryBox.addEventListener('click', () => {
    console.log('Summary panel clicked');
  });
});