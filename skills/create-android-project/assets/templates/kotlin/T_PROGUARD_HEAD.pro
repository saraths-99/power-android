# R8 rules for the release build.
#
# The AndroidX libraries, Hilt and Room all ship their own consumer rules, so
# this file only needs project-specific keeps.

# Keep Kotlin metadata so reflection-based libraries keep working.
-keepattributes RuntimeVisibleAnnotations,AnnotationDefault,Signature,InnerClasses,EnclosingMethod
