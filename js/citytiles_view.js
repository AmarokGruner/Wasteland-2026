// Simple CityTiles renderer for a 15x15 province map
(function(){
  const SIZE = 15;
  const board = document.getElementById('board');
  // build grid
  for(let y=0;y<SIZE;y++){
    for(let x=0;x<SIZE;x++){
      const c = document.createElement('div');
      c.className = 'cell land';
      c.dataset.x = x;
      c.dataset.y = y;
      board.appendChild(c);
    }
  }

  // helper to set citytile style on coords
  function markCityTiles(coords, stage){
    if(!coords) return;
    coords.forEach(([cx, cy]) => {
      const el = board.querySelector(`.cell[data-x='${cx}'][data-y='${cy}']`);
      if(el){ el.classList.add(`city-${stage}`); }
    });
  }

  // fetch citytiles for province 1 (token from localStorage or query param)
  const token = (typeof localStorage !== 'undefined') ? localStorage.getItem('token') : '';
  fetch(`/province/1/citytiles${token ? '?token=' + token : ''}`)
    .then(r => r.json())
    .then(data => {
      if(!data || !data.citytiles) return;
      data.citytiles.forEach(ct => {
        // coords is an array of [x,y]
        markCityTiles(ct.coords, ct.stage);
      });
    })
    .catch(() => {
      console.warn('CityTiles fetch failed. Ensure API is available and token is valid.');
    });
})();
