#include <cstddef>

#if defined(_WIN32)
#define MID_EXPORT __declspec(dllexport)
#else
#define MID_EXPORT __attribute__((visibility("default")))
#endif

extern "C" {

MID_EXPORT int mid_build_lagged_design(
    const double* values,
    std::size_t n_rows,
    std::size_t n_cols,
    std::size_t lags,
    double* x_out,
    double* y_out) {
    if (values == nullptr || x_out == nullptr || y_out == nullptr) {
        return -1;
    }
    if (lags == 0 || n_rows <= lags || n_cols == 0) {
        return -2;
    }

    const std::size_t n_samples = n_rows - lags;
    const std::size_t x_width = lags * n_cols;

    for (std::size_t sample = 0; sample < n_samples; ++sample) {
        const std::size_t t = sample + lags;

        for (std::size_t lag = 1; lag <= lags; ++lag) {
            const std::size_t source_row = t - lag;
            const std::size_t x_offset = sample * x_width + (lag - 1) * n_cols;
            const std::size_t source_offset = source_row * n_cols;
            for (std::size_t col = 0; col < n_cols; ++col) {
                x_out[x_offset + col] = values[source_offset + col];
            }
        }

        const std::size_t y_offset = sample * n_cols;
        const std::size_t source_offset = t * n_cols;
        for (std::size_t col = 0; col < n_cols; ++col) {
            y_out[y_offset + col] = values[source_offset + col];
        }
    }

    return 0;
}

MID_EXPORT int mid_native_abi_version() {
    return 1;
}

}  // extern "C"
