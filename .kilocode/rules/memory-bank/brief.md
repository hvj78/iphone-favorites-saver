This project is a simple commmand line python application for the following purpose: migrate favorites status and image description from iPhone's Photos.sqlite database into the exif info of the images copied from the iPhone to the PC

The application excepts, that the user already copied all the images and videos from the iPhone to the PC keeping the original folder structure and file names.

It uses the following libraries:
- sqlite3 for accessing the iPhone's Photos.sqlite database
- exiftool for reading and writing EXIF data

The application has the following features:
1. Migrate favorites status from Photos.sqlite to EXIF data
2. Migrate image descriptions from Photos.sqlite to EXIF data
3. Check the destination image and check if rating and description is present
4. if a rating or a description is present already, display to the console the rating and description and ask user if he wants to overwrite them or keep the existing ones

The application is designed to be run as a single command.

Command line options:
- Photos.sqlite (the database file might have been renamed, so the user has to provide the database file as an option)
- location of the photos: the directory under the 100APPLE folders can be found.

