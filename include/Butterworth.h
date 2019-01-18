#include <vector>
#include <cstdint>

#include <boost/python.hpp>
#include <boost/python/numpy.hpp>

namespace bp = boost::python;
namespace np = boost::python::numpy;

using namespace std;

class BFilterParams {
public:
    BFilterParams(int32_t b0, int32_t b1, int b_bits, int p_bits, int shift)
        : b0{b0}, b1{b1}, b_bits{b_bits}, p_bits{p_bits}, shift{shift} {}
    int32_t b0;
    int32_t b1;
    int b_bits;
    int p_bits;
    int shift;
};

class BFilterBank {
public:
    BFilterBank() {}
    BFilterBank(const BFilterBank& a);
    BFilterBank& add(BFilterParams par);
    BFilterBank& init(int n_chan);
    void apply(int32_t* input, int32_t* output, int n_samp);
    void apply_to_float(float *input, float *output, float unit, int n_samp);

    void apply_numpy(np::ndarray& input, np::ndarray& output);

    std::vector<vector<array<int64_t,2>>> w;  // (n_bank,n_chan,2)
    std::vector<BFilterParams> par;
};

void butterworth_test();
