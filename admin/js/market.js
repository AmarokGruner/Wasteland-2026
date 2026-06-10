(function () {
    const api = '/admin/market';          // correct prefix, no extra /api/
    const tbody = document.querySelector('#market-table tbody');

    function load() {
        fetch(api, { credentials: 'include' })
            .then(r => r.json())
            .then(data => {
                tbody.innerHTML = '';
                data.offers.forEach(o => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `<td>${o.name}</td>
                                    <td>${o.buy_price}</td>
                                    <td><button onclick="sell(${o.id})">Sell</button></td>`;
                    tbody.appendChild(tr);
                });
            })
            .catch(console.error);
    }

    window.sell = function (id) {
        fetch(`${api}/sell/${id}`, { method: 'POST', credentials: 'include' })
            .then(r => r.json())
            .then(resp => console.log('sell result', resp))
            .catch(console.error);
    };

    load();
})();
JS