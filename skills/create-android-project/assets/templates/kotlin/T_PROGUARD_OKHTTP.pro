
# OkHttp (via Retrofit) references optional TLS providers that are not on the
# classpath. Without these, R8 treats the missing classes as errors.
-dontwarn org.bouncycastle.jsse.**
-dontwarn org.conscrypt.**
-dontwarn org.openjsse.**
