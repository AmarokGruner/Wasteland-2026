export function applyRandomDeaths(province: any): void {
  const deathsKinder = Math.ceil(0.0007 * province.bevoelkerung.kinder);
  const deathsErwachsen = Math.ceil(0.001 * province.bevoelkerung.erwachsen);
  const deathsRentner = Math.ceil(0.002 * province.bevoelkerung.rentner);

  province.tode.kind = deathsKinder;
  province.tode.erwachsen = deathsErwachsen;
  province.tode.rentner = deathsRentner;
}
