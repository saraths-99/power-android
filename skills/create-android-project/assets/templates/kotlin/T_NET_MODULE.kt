package {{PKG_NET_DI}}

import {{PKG_NET}}.ItemRemoteDataSource
import {{PKG_NET}}.retrofit.RetrofitItemRemoteDataSource
import dagger.Binds
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import kotlinx.serialization.json.Json
import okhttp3.Call
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
internal object NetworkModule {

    @Provides
    @Singleton
    fun providesNetworkJson(): Json = Json {
        ignoreUnknownKeys = true
    }

    @Provides
    @Singleton
    fun providesCallFactory(): Call.Factory = OkHttpClient.Builder()
        .addInterceptor(
            HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BASIC
            },
        )
        .build()
}

@Module
@InstallIn(SingletonComponent::class)
internal interface NetworkBindsModule {

    @Binds
    fun bindsItemRemoteDataSource(
        impl: RetrofitItemRemoteDataSource,
    ): ItemRemoteDataSource
}
