// Recover the 64 license indices from the 62 mod-257 invariants and
// the Hamiltonian-cycle condition in sub_21C0.
#include <array>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <string>

constexpr int P = 257, N = 64, R = 62;
constexpr char ABC[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-";

int mod(int x) { x %= P; return x < 0 ? x + P : x; }
int inv(int x) {
    for (int i = 1; i < P; ++i) if (i * x % P == 1) return i;
    return 0;
}
uint16_t word(const std::string &b, int off) {
    return static_cast<unsigned char>(b[off]) | (static_cast<unsigned char>(b[off+1]) << 8);
}

int main(int argc, char **argv) {
    std::ifstream file(argc > 1 ? argv[1] : "challenge", std::ios::binary);
    std::string b((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());
    if (b.size() < 0x4ba8) { std::fprintf(stderr, "Cannot read challenge\n"); return 1; }
    int a[R][N+1]{};
    for (int k = 0; k < R; ++k) {
        for (int i = 0; i < 8; ++i)
            for (int j = 0; j < 8; ++j)
                a[k][i*8+j] = word(b, 0x4640 + 16*k + 2*i) * word(b, 0x4260 + 16*k + 2*j) % P;
        a[k][N] = word(b, 0x41e0 + 2*k);
    }
    int rank = 0, piv[R]{};
    bool is_pivot[N]{};
    for (int col = 0; col < N && rank < R; ++col) {
        int found = rank;
        while (found < R && a[found][col] == 0) ++found;
        if (found == R) continue;
        for (int c = 0; c <= N; ++c) std::swap(a[rank][c], a[found][c]);
        int factor = inv(a[rank][col]);
        for (int c = 0; c <= N; ++c) a[rank][c] = a[rank][c] * factor % P;
        for (int r = 0; r < R; ++r) if (r != rank && a[r][col]) {
            factor = a[r][col];
            for (int c = 0; c <= N; ++c) a[r][c] = mod(a[r][c] - factor * a[rank][c]);
        }
        piv[rank] = col;
        is_pivot[col] = true;
        ++rank;
    }
    int free_col[4], nf = 0;
    for (int col = 0; col < N; ++col) if (!is_pivot[col]) free_col[nf++] = col;
    std::printf("rank=%d free=%d", rank, nf);
    for (int j = 0; j < nf; ++j) std::printf(" %d", free_col[j]);
    std::puts("");
    if (rank != 60 || nf != 4) return 1;

    int x[N]{};
    uint64_t bounded = 0, cycles = 0;
    for (int u = 1; u <= 62; ++u) for (int v = 1; v <= 62; ++v)
    for (int w = 1; w <= 62; ++w) for (int z = 1; z <= 62; ++z) {
        x[free_col[0]] = u; x[free_col[1]] = v;
        x[free_col[2]] = w; x[free_col[3]] = z;
        bool good = true;
        int digits = (u >= 53) + (v >= 53) + (w >= 53) + (z >= 53);
        for (int r = 0; r < rank; ++r) {
            int q = a[r][N];
            for (int j = 0; j < 4; ++j) q -= a[r][free_col[j]] * x[free_col[j]];
            q = mod(q);
            if (q < 1 || q > 62) { good = false; break; }
            x[piv[r]] = q;
            digits += q >= 53;
        }
        if (!good) continue;
        ++bounded;
        if (digits != 13) continue;
        int counts[63]{};
        for (int i = 0; i < N; ++i) if (++counts[x[i]] > 4) { good = false; break; }
        if (!good) continue;
        int pos = 0;
        uint64_t seen = 0;
        for (int i = 0; i < N; ++i) {
            uint64_t bit = uint64_t(1) << pos;
            if (seen & bit) { good = false; break; }
            seen |= bit;
            pos = (pos + x[pos]) & 63;
        }
        if (!good || pos != 0 || seen != UINT64_MAX) continue;
        ++cycles;
        for (int i = 0; i < N; ++i) std::putchar(ABC[x[i]-1]);
        std::putchar('\n');
        std::fflush(stdout);
    }
    std::fprintf(stderr, "bounded=%llu cycles=%llu\n", (unsigned long long)bounded, (unsigned long long)cycles);
}
