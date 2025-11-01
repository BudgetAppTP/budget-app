(function(){
  var el = document.getElementById("charts-data");
  if(!el) return;
  var data = JSON.parse(el.textContent || "{}");

  function pieSections(ctx){
    var labels = Object.keys(data.sections || {});
    var values = labels.map(function(k){ return Number(data.sections[k] || 0); });
    return new Chart(ctx, {
      type: "pie",
      data: {
        labels: labels,
        datasets: [{ data: values }]
      },
      options: { responsive: true, maintainAspectRatio: false }
    });
  }

  function barCategories(ctx){
    var labels = Object.keys(data.cats_exp || {});
    var values = labels.map(function(k){ return Number(data.cats_exp[k] || 0); });
    return new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [{ label: "Vydavky", data: values }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: { beginAtZero: true } }
      }
    });
  }

  function lineTrend(ctx){
    var labels = data.months || [];
    var inc = (data.series_inc || []).map(Number);
    var exp = (data.series_exp || []).map(Number);
    return new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          { label: "Prijmy", data: inc },
          { label: "Vydavky", data: exp }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: { beginAtZero: true } }
      }
    });
  }

  var c1 = document.getElementById("pieSections");
  var c2 = document.getElementById("barCategories");
  var c3 = document.getElementById("lineTrend");
  if (c1) pieSections(c1.getContext("2d"));
  if (c2) barCategories(c2.getContext("2d"));
  if (c3) lineTrend(c3.getContext("2d"));
})();
