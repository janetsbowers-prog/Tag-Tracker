"""
Database Seeding Script for CSI Color Vault
Imports color formula data from CSV file into the database
"""
import csv
import os
import sys
from app import app
from database import db, ColorFormula

def seed_database(csv_filepath):
    """
    Read CSV file and populate database with color formulas
    
    CSV Format Expected:
    Card No, Color Name, Color Number, Season, Formula 1, Formula 2, Formula 3
    """
    with app.app_context():
        # Clear existing data (optional - comment out if you want to keep existing records)
        # ColorFormula.query.delete()
        # db.session.commit()
        
        records_added = 0
        records_skipped = 0
        
        with open(csv_filepath, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                try:
                    # Combine the three formula columns into one
                    formula_parts = []
                    if row.get('Formula 1'):
                        formula_parts.append(row['Formula 1'])
                    if row.get('Formula 2'):
                        formula_parts.append(row['Formula 2'])
                    if row.get('Formula 3'):
                        formula_parts.append(row['Formula 3'])
                    
                    combined_formula = '\n'.join(formula_parts)
                    
                    # Check if this color number already exists
                    existing = ColorFormula.query.filter_by(
                        color_number=row['Color Number']
                    ).first()
                    
                    if existing:
                        print(f"Skipping {row['Color Number']} - {row['Color Name']} (already exists)")
                        records_skipped += 1
                        continue
                    
                    # Create new formula record
                    new_formula = ColorFormula(
                        color_name=row['Color Name'],
                        color_number=row['Color Number'],
                        formula=combined_formula,
                        raw_text=f"Color Name: {row['Color Name']}\nColor Number: {row['Color Number']}\nFormula: {combined_formula}"
                    )
                    
                    db.session.add(new_formula)
                    records_added += 1
                    print(f"Added: {row['Color Number']} - {row['Color Name']}")
                    
                except Exception as e:
                    print(f"Error processing row {row.get('Card No', '?')}: {e}")
                    continue
        
        # Commit all changes
        db.session.commit()
        
        print(f"\n✅ Seeding complete!")
        print(f"   Records added: {records_added}")
        print(f"   Records skipped: {records_skipped}")
        print(f"   Total in database: {ColorFormula.query.count()}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python seed_database.py <path_to_csv_file>")
        print("Example: python seed_database.py formulas.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    if not os.path.exists(csv_file):
        print(f"❌ Error: File '{csv_file}' not found!")
        sys.exit(1)
    
    print(f"📂 Reading CSV file: {csv_file}")
    print(f"🗄️  Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print()
    
    confirm = input("Proceed with seeding? (yes/no): ")
    if confirm.lower() == 'yes':
        seed_database(csv_file)
    else:
        print("Cancelled.")
