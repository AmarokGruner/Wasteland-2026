import { validateField, fieldConfig, FieldType } from './field-types';

describe('FieldType enum', () => {
  const types: FieldType[] = [
    FieldType.Building,
    FieldType.City,
    FieldType.Weg,
    FieldType.Kreuzung,
  ];

  it('should contain all defined field types', () => {
    // Object.values should match the expected enum values
    const expected = [
      'gebaeude',
      'stadt',
      'weg',
      'kreuzung',
    ];
    expect(Object.values(fieldConfig)).toEqual(expected);
  });
});

describe('Field validation logic', () => {
  const validBuilding = {
    dbId: 'gebaeude',
    size: { width: 40, height: 40 },
    buildable: true,
    category: 'Land',
    color: '#5a7a3a',
  };

  const validCity = {
    dbId: 'stadt',
    size: { width: 40, height: 40 },
    buildable: true,
    category: 'Stadt',
    color: '#6a6a8a',
  };

  const validWegHorizontal = {
    dbId: 'weg',
    size: { width: 40, height: 10 },
    buildable: true,
    category: 'Infrastruktur',
    color: '#8b7355',
  };

  const validKreuzung = {
    dbId: 'kreuzung',
    size: { width: 10, height: 10 },
    buildable: true,
    category: 'Infrastruktur',
    color: '#7a6345',
  };

  it('validates a correct building field', () => {
    const result = validateField(validBuilding as any);
    expect(result).toBe(true);
  });

  it('rejects a building field with wrong width', () => {
    const invalid = { ...validBuilding, size: { width: 30, height: 40 } };
    expect(validateField(invalid as any)).toBe(false);
  });

  it('rejects a building field with wrong height', () => {
    const invalid = { ...validBuilding, size: { width: 40, height: 30 } };
    expect(validateField(invalid as any)).toBe(false);
  });

  it('rejects a building field with non‑buildable flag', () => {
    const invalid = { ...validBuilding, buildable: false };
    expect(validateField(invalid as any)).toBe(false);
  });

  it('validates a correct city field', () => {
    const result = validateField(validCity as any);
    expect(result).toBe(true);
  });

  it('validates a correct way field (horizontal)', () => {
    const result = validateField(validWegHorizontal as any);
    expect(result).toBe(true);
  });

  it('validates a correct crossing field', () => {
    const result = validateField(validKreuzung as any);
    expect(result).toBe(true);
  });

  it('rejects an unknown dbId', () => {
    const unknown = {
      dbId: 'unknown',
      size: { width: 40, height: 40 },
      buildable: true,
      category: 'Land',
      color: '#ffffff',
    };
    expect(validateField(unknown as any)).toBe(false);
  });

  it('rejects a way field with incorrect dimensions', () => {
    const invalid = { ...validWegHorizontal, size: { width: 20, height: 10 } };
    expect(validateField(invalid as any)).toBe(false);
  });

  it('rejects a kreuzung field with incorrect dimensions', () => {
    const invalid = { ...validKreuzung, size: { width: 15, height: 10 } };
    expect(validateField(invalid as any)).toBe(false);
  });
});
