#!/bin/bash
# Script to help migrate remaining modules to the src-based layout

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a directory exists
check_directory() {
    if [ -d "$1" ]; then
        return 0
    else
        return 1
    fi
}

# Function to create directory if it doesn't exist
create_directory() {
    if [ ! -d "$1" ]; then
        mkdir -p "$1"
        echo -e "${GREEN}Created directory:${NC} $1"
    else
        echo -e "${BLUE}Directory already exists:${NC} $1"
    fi
}

# Function to migrate a module
migrate_module() {
    local src_path="$1"
    local dest_path="$2"
    
    # Check if source exists
    if [ ! -d "$src_path" ]; then
        echo -e "${RED}Source directory not found:${NC} $src_path"
        return 1
    fi
    
    # Create destination directory if it doesn't exist
    create_directory "$dest_path"
    
    # Copy files
    echo -e "${YELLOW}Copying files from${NC} $src_path ${YELLOW}to${NC} $dest_path"
    cp -r "$src_path"/* "$dest_path"/ 2>/dev/null
    
    # Check for __init__.py
    if [ ! -f "$dest_path/__init__.py" ]; then
        echo -e "${YELLOW}Creating __init__.py in${NC} $dest_path"
        touch "$dest_path/__init__.py"
    fi
    
    echo -e "${GREEN}Successfully migrated:${NC} $src_path ${GREEN}→${NC} $dest_path"
}

# Main migration function
migrate_remaining_modules() {
    local repo_root="$1"
    
    echo -e "${BLUE}=== Starting Migration of Remaining Modules ===${NC}"
    
    # Create base directories if they don't exist
    create_directory "$repo_root/src/ailf"
    create_directory "$repo_root/src/ailf/schemas"
    
    # List of modules to migrate from ailf/ to src/ailf/
    ailf_modules=(
        "cognition"
        "communication"
        "feedback" 
        "interaction"
        "memory"
        "registry_client"
        "routing"
    )
    
    # Migrate ailf modules
    for module in "${ailf_modules[@]}"; do
        migrate_module "$repo_root/ailf/$module" "$repo_root/src/ailf/$module"
    done
    
    # List of modules to migrate from utils/ to appropriate src/ailf/ locations
    utils_modules=(
        "ai"
        "core"
        "cloud"
        "messaging"
        "storage"
        "workers"
    )
    
    # Migrate utils modules
    for module in "${utils_modules[@]}"; do
        migrate_module "$repo_root/utils/$module" "$repo_root/src/ailf/$module"
    done
    
    # Special case for utils/__init__.py which might have important exports
    if [ -f "$repo_root/utils/__init__.py" ]; then
        echo -e "${YELLOW}Checking utils/__init__.py for exports...${NC}"
        # Create a backup of the src/ailf/__init__.py if it exists
        if [ -f "$repo_root/src/ailf/__init__.py" ]; then
            cp "$repo_root/src/ailf/__init__.py" "$repo_root/src/ailf/__init__.py.bak"
            echo -e "${GREEN}Created backup of src/ailf/__init__.py${NC}"
        fi
    fi
    
    # Migrate schema files if not already migrated
    if [ -d "$repo_root/schemas" ]; then
        echo -e "${YELLOW}Migrating schema files...${NC}"
        for schema_file in "$repo_root/schemas"/*.py; do
            if [ -f "$schema_file" ]; then
                base_name=$(basename "$schema_file")
                if [ ! -f "$repo_root/src/ailf/schemas/$base_name" ]; then
                    echo -e "${YELLOW}Copying${NC} $base_name ${YELLOW}to${NC} src/ailf/schemas/"
                    cp "$schema_file" "$repo_root/src/ailf/schemas/"
                fi
            fi
        done
    fi
    
    # Fix imports in migrated files
    echo -e "${BLUE}=== Updating Import Statements ===${NC}"
    fix_imports "$repo_root"
    
    echo -e "${BLUE}=== Migration Complete ===${NC}"
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Review updated import statements in the migrated files"
    echo "2. Test the migrated modules"
    echo "3. Update the migration report"
    echo "4. Update src/ailf/__init__.py to expose the right imports"
}

# Function to fix imports in migrated files
fix_imports() {
    local repo_root="$1"
    echo -e "${YELLOW}Fixing imports in migrated Python files...${NC}"
    
    # Find all Python files in the src/ailf directory
    find "$repo_root/src/ailf" -name "*.py" -type f | while read -r file; do
        echo -e "${BLUE}Updating imports in${NC} $file"
        
        # Replace common import patterns
        sed -i 's/from utils\.core/from ailf.core/g' "$file"
        sed -i 's/from utils\.ai/from ailf.ai/g' "$file"
        sed -i 's/from utils\.cloud/from ailf.cloud/g' "$file"
        sed -i 's/from utils\.messaging/from ailf.messaging/g' "$file"
        sed -i 's/from utils\.storage/from ailf.storage/g' "$file"
        sed -i 's/from utils\.workers/from ailf.workers/g' "$file"
        
        sed -i 's/import utils\.core/import ailf.core/g' "$file"
        sed -i 's/import utils\.ai/import ailf.ai/g' "$file"
        sed -i 's/import utils\.cloud/import ailf.cloud/g' "$file"
        sed -i 's/import utils\.messaging/import ailf.messaging/g' "$file"
        sed -i 's/import utils\.storage/import ailf.storage/g' "$file"
        sed -i 's/import utils\.workers/import ailf.workers/g' "$file"
        
        # Replace schema imports
        sed -i 's/from schemas\./from ailf.schemas./g' "$file"
        sed -i 's/import schemas\./import ailf.schemas./g' "$file"
    done
    
    echo -e "${GREEN}Import statements updated${NC}"
}

# Execute the migration
if [ -z "$1" ]; then
    # Default to current repository root if no path provided
    repo_root="$(pwd)"
else
    repo_root="$1"
fi

echo -e "${BLUE}Starting migration for repository at:${NC} $repo_root"
migrate_remaining_modules "$repo_root"
