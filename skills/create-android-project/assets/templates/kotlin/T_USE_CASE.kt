package {{PKG_USECASE}}

{{USE_CASE_IMPORTS}}import javax.inject.Inject

/** {{USE_CASE_DOC}} */
class {{USE_CASE_NAME}} @Inject constructor(
    private val repository: {{USE_CASE_REPO}},
) {
    {{USE_CASE_SIGNATURE}} = {{USE_CASE_BODY}}
}
