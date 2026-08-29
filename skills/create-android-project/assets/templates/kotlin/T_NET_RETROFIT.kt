package {{PKG_NET}}.retrofit

import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import {{PKG_NET}}.ItemRemoteDataSource
import {{PKG_NET}}.model.ItemDto
import kotlinx.serialization.json.Json
import okhttp3.Call
import okhttp3.MediaType.Companion.toMediaType
import retrofit2.Retrofit
import retrofit2.http.GET
import javax.inject.Inject
import javax.inject.Singleton

// TODO: point this at your real backend.
private const val BASE_URL = "https://example.com/api/"

private interface ItemApi {
    @GET("items")
    suspend fun getItems(): List<ItemDto>
}

@Singleton
internal class RetrofitItemRemoteDataSource @Inject constructor(
    networkJson: Json,
    callFactory: Call.Factory,
) : ItemRemoteDataSource {

    private val api = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .callFactory { request -> callFactory.newCall(request) }
        .addConverterFactory(networkJson.asConverterFactory("application/json".toMediaType()))
        .build()
        .create(ItemApi::class.java)

    override suspend fun fetchItems(): List<ItemDto> = api.getItems()
}
