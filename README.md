# Discogs CSV Generator

A Python script that generates CSV files with Discogs release information following best practices.

## Features

- Generates properly formatted CSV files
- Includes all required fields from template
- Follows PEP 8 style guidelines
- Uses type hints for better code clarity
- Validates input before file operations
- Handles errors gracefully

## Usage

```bash
# Generate CSV with default filename
python generate_csv.py

# Generate CSV with custom output path
python generate_csv.py --output my_discogs_data.csv
```

## Requirements

See [`requirements.txt`](requirements.txt) for dependency information.

## Output Format

The generated CSV follows the structure in [`Discogs_overview_template.csv`](Discogs_overview_template.csv):

- Standard Discogs release fields
- URL links for releases
- Artist and album information
- Icon paths and formatting options
- Color space and reliability settings

## Best Practices Implemented

1. **Type Safety**: Uses Python type hints throughout
2. **Error Handling**: Proper validation and exception handling
3. **Input Validation**: Checks CSV filename extension before writing
4. **Modular Design**: Separates data generation from file writing
5. **Documentation**: Clear docstrings for all functions
6. **Encoding**: Explicit UTF-8 encoding for proper character handling
7. **CLI Interface**: Uses argparse for flexible command-line options

## Example Output

See the sample data in [`Discogs_overview_template.csv`](Discogs_overview_template.csv) lines 2-22 for what the generated CSV will look like.
