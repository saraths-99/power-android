package {{PKG_DATA_DI}}

{{REPO_MODULE_IMPORTS}}import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent

/** Binds repository interfaces to their implementations. */
@Module
@InstallIn(SingletonComponent::class)
internal interface RepositoryModule {

{{REPO_BINDS}}
}
