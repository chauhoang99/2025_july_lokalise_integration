import pandas as pd
import json
from pathlib import Path
from typing import Dict, List

def excel_to_json(excel_file: str, output_file: str = None) -> Dict:
    """
    Convert Excel file to JSON format suitable for Lokalise
    
    Args:
        excel_file: Path to the Excel file
        output_file: Optional path to save JSON file
        
    Returns:
        Dict containing the converted data
    """
    try:
        # Read Excel file
        df = pd.read_excel(excel_file)
        
        # Print column names for debugging
        print("Available columns:", df.columns.tolist())
        
        # Clean column names (remove whitespace and special characters)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        print("Cleaned columns:", df.columns.tolist())
        
        # Print first few rows for debugging
        print("\nFirst few rows:")
        print(df.head())
        
        # Convert to dictionary format
        translations = {
            "translations": []
        }
        
        # Process each row
        for idx, row in df.iterrows():
            # Skip rows with missing key terms
            if pd.isna(row.get('term', '')):
                continue
                
            entry = {
                "term": str(row['term']).strip(),
                "part_of_speech": str(row.get('part_of_speech', '')).strip() if not pd.isna(row.get('part_of_speech', '')) else None,
                "description": str(row.get('description', '')).strip() if not pd.isna(row.get('description', '')) else None,
                "translations": []
            }
            
            # Print row data for debugging
            print(f"\nProcessing row {idx}:")
            print(row.to_dict())
            
            # Add translations if available
            for lang in ['en', 'es', 'fr', 'de', 'it', 'ja', 'ko', 'zh']:
                # Try different possible column name formats for translations
                possible_translation_columns = [
                    f'translation_{lang}',
                    f'{lang}_translation',
                    f'{lang}',
                    lang.upper(),
                    f'translation_in_{lang}',
                    f'{lang}_text'
                ]
                
                # Try different possible column name formats for descriptions
                possible_description_columns = [
                    f'description_{lang}',
                    f'{lang}_description',
                    f'{lang}_notes',
                    f'notes_{lang}',
                    f'{lang}_comment',
                    f'comment_{lang}'
                ]
                
                translation_value = None
                description_value = None
                used_translation_column = None
                used_description_column = None
                
                # Find translation
                for col in possible_translation_columns:
                    if col in row.index and not pd.isna(row[col]):
                        translation_value = str(row[col]).strip()
                        used_translation_column = col
                        break
                
                # Find description
                for col in possible_description_columns:
                    if col in row.index and not pd.isna(row[col]):
                        description_value = str(row[col]).strip()
                        used_description_column = col
                        break
                
                if translation_value:
                    print(f"Found translation for {lang} in column {used_translation_column}: {translation_value}")
                    if description_value:
                        print(f"Found description for {lang} in column {used_description_column}: {description_value}")
                    
                    translation_entry = {
                        "language_iso": lang,
                        "translation": translation_value
                    }
                    
                    if description_value:
                        translation_entry["description"] = description_value
                        
                    entry["translations"].append(translation_entry)
            
            translations["translations"].append(entry)
        
        # Save to file if output path is provided
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(translations, f, ensure_ascii=False, indent=2)
        
        return translations
        
    except Exception as e:
        raise Exception(f"Error converting Excel to JSON: {str(e)}")

def main():
    """
    Main function to run the conversion
    """
    # Get the root directory
    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    
    # Input and output paths
    input_file = root_dir / "Practical Test Glossary - Localization Technical Specialist - 20250601 (2).xlsx"
    output_file = root_dir / "glossary.json"
    
    try:
        result = excel_to_json(str(input_file), str(output_file))
        print(f"\nSuccessfully converted Excel to JSON. Output saved to {output_file}")
        print(f"Total terms processed: {len(result['translations'])}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 