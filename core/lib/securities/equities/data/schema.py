# Various local schemas used for returned data

ADJUSTMENTS_SCHEMA = {
  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "Date": {
      "description": "Adjustment date",
      "type": "datetime"
    },
    "Dividend": {
      "description": "Value for adjusted dividend",
      "type": "number"
    },
    "Price Adjustment": {
      "convert_name": "PriceAdjustment",
      "description": "Factor by which raw dividend amounts are multiplied to get their adjusted values",
      "type": "number"
    },
    "Volume Adjustment": {
      "convert_name": "VolumeAdjustment",
      "description": "Factor by which raw volume is multiplied to get its adjusted value",
      "type": "number"
    }
  },
  "oneOf": [
    {"required": [ "Dividend" ]},
    {"required": [ "Price Adjustment", "Volume Adjustment" ]}
  ],
  "required": [
    "Date"
  ]
}
DIVIDENDS_SCHEMA = {
  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "Adjusted Dividend": {
      "convert_name": "AdjustedDividend",
      "db_order": 3,
      "description": "Amount of cash dividend accounting for splits",
      "type": "number"
    },
    "Date": {
      "db_order": 1,
      "description": "Dividend date",
      "type": "datetime"
    },
    "Dividend": {
      "db_order": 2,
      "description": "Amount of cash dividend in US dollars",
      "type": "number"
    }
  },
  "required": [
    "Date",
    "Dividend"
  ]
}

SPLITS_SCHEMA = {
  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "Date": {
      "db_order": 1,
      "description": "Split date",
      "type": "datetime"
    },
    "Denominator": {
      "db_order": 3,
      "description": "The starting proportion of shares to be split",
      "type": "integer"
    },
    "Numerator": {
      "db_order": 2,
      "description": "The ending proportion of shares outstanding after the split",
      "type": "integer"
    },
    "Price Dividend Adjustment": {
      "convert_name": "PriceDividendAdjustment",
      "db_order": 4,
      "description": "Factor by which raw prices and dividend amounts are multiplied to get their adjusted values before the split",
      "type": "number"
    },
    "Volume Adjustment": {
      "convert_name": "VolumeAdjustment",
      "db_order": 5,
      "description": "Factor by which raw volume is multiplied to get its adjusted value before the split",
      "type": "number"
    }
  },
  "required": [
    "Date",
    "Denominator",
    "Numerator",
    "Price Dividend Adjustment",
    "Volume Adjustment"
  ]
}

class SchemaParser():

    def database_format_columns(self,schema):
        db_columns = {}
        for key in schema['properties']:
            if 'db_order' not in schema['properties'][key]:
                continue
            db_columns[schema['properties'][key]['db_order']] = key
        columns = []
        for key in sorted(db_columns):
            columns.append(db_columns[key])
        return columns
