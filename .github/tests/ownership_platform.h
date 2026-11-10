#import <Carbon/Carbon.h>
#import <Cocoa/Cocoa.h>

// Redirect native image and filesystem boundaries before any actual source.
@interface OwnershipURL : NSObject
- (id)initWithString:(NSString *)value;
- (NSString *)absoluteString;
@end
@interface OwnershipImage : NSObject
- (id)initWithCGImage:(CGImageRef)image size:(NSSize)size;
- (NSData *)TIFFRepresentation;
@end
CFURLRef OwnershipCreateURL(CFAllocatorRef, CFStringRef, CFURLPathStyle, Boolean);
CFStringRef OwnershipCopyPath(CFURLRef, CFURLPathStyle);
#define NSURL OwnershipURL
#define NSImage OwnershipImage
#define CFURLCreateWithFileSystemPath OwnershipCreateURL
#define CFURLCopyFileSystemPath OwnershipCopyPath
