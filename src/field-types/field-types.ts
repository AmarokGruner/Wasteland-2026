export enum FieldType {
  Building = 'gebaeude',
  City = 'stadt',
  Weg = 'weg',
  Kreuzung = 'kreuzung',
}

export enum FieldCategory {
  Land,
  Stadt,
  Infrastruktur,
}

export interface Field {
  dbId: string;
  size: { width: number; height: number; };
  buildable: boolean;
  category: FieldCategory;
  color: string;
}

export const fieldConfig: Record<FieldType, Field> = {
  [FieldType.Building]: {
    dbId: 'gebaeude',
    size: { width: 40, height: 40 },
    buildable: true,
    category: FieldCategory.Land,
    color: '#5a7a3a',
  },
  [FieldType.City]: {
    dbId: 'stadt',
    size: { width: 40, height: 40 },
    buildable: true,
    category: FieldCategory.Stadt,
    color: '#6a6a8a',
  },
  [FieldType.Weg]: {
    dbId: 'weg',
    size: { width: 40, height: 10 },
    buildable: true,
    category: FieldCategory.Infrastruktur,
    color: '#8b7355',
  },
  [FieldType.Kreuzung]: {
    dbId: 'kreuzung',
    size: { width: 10, height: 10 },
    buildable: true,
    category: FieldCategory.Infrastruktur,
    color: '#7a6345',
  },
};

export function validateField(field: Field): boolean {
  const cfg = fieldConfig[field.dbId as FieldType];
  return cfg !== undefined && field.size.width === cfg.size.width && field.size.height === cfg.size.height && field.buildable === cfg.buildable;
}
