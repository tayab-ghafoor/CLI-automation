#!/bin/bash
# System Manager CLI - Unix/Mac Runner

show_menu() {
    clear
    echo ""
    echo "================================================"
    echo "  SYSTEM MANAGER CLI - Interactive Menu"
    echo "================================================"
    echo ""
    echo "1. Check System Health"
    echo "2. Clean Temporary Files"
    echo "3. Backup Folder"
    echo "4. Generate System Report"
    echo "5. Setup Configuration"
    echo "6. Exit"
    echo ""
    read -p "Select an option (1-6): " choice
}

while true; do
    show_menu
    
    case $choice in
        1)
            clear
            echo "Checking system health..."
            python3 main.py check-health
            echo ""
            read -p "Press Enter to continue..."
            ;;
        2)
            clear
            read -p "Enter folder path to clean: " folder
            if [ -d "$folder" ]; then
                python3 main.py clean-temp "$folder"
            else
                echo "Error: Folder not found"
            fi
            echo ""
            read -p "Press Enter to continue..."
            ;;
        3)
            clear
            read -p "Enter folder path to backup: " source
            if [ -d "$source" ]; then
                read -p "Compress the backup? (y/n): " compress
                if [ "$compress" = "y" ]; then
                    python3 main.py backup-folder "$source" --compress
                else
                    python3 main.py backup-folder "$source"
                fi
            else
                echo "Error: Folder not found"
            fi
            echo ""
            read -p "Press Enter to continue..."
            ;;
        4)
            clear
            read -p "Enter log file or folder path: " logpath
            if [ -e "$logpath" ]; then
                python3 main.py generate-report "$logpath" --export
            else
                echo "Error: Path not found"
            fi
            echo ""
            read -p "Press Enter to continue..."
            ;;
        5)
            clear
            echo "Running setup..."
            python3 main.py setup
            echo ""
            read -p "Press Enter to continue..."
            ;;
        6)
            echo "Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid choice. Please try again."
            ;;
    esac
done
