use pyo3::prelude::*;
use pyo3::types::PyBytes;

// ── GF(2) матричный движок ────────────────────────────────────────────

const GF2_DIM: usize = 32;
type Gf2Mat = [u32; GF2_DIM];

fn mat_times(mat: &Gf2Mat, mut vec: u32) -> u32 {
    let mut s = 0u32;
    let mut i = 0;
    while vec != 0 {
        if vec & 1 != 0 {
            s ^= mat[i];
        }
        vec >>= 1;
        i += 1;
    }
    s
}

fn mat_square(src: &Gf2Mat) -> Gf2Mat {
    let mut dst = [0u32; GF2_DIM];
    for i in 0..GF2_DIM {
        dst[i] = mat_times(src, src[i]);
    }
    dst
}

// Базовая матрица — строится один раз при загрузке модуля
fn build_base_odd() -> Gf2Mat {
    let mut odd = [0u32; GF2_DIM];
    odd[0] = 0xEDB88320u32;          // CRC-32 polynomial
    for i in 1..GF2_DIM {
        odd[i] = 1 << (i - 1);
    }
    let even = mat_square(&odd);
    mat_square(&even)                // 4-битный оператор
}

fn crc32_combine(mut crc1: u32, crc2: u32, mut len2: u64, base: &Gf2Mat) -> u32 {
    if len2 == 0 {
        return crc1;
    }
    let mut odd = *base;             // копия за O(32×4 байта)
    loop {
        let even = mat_square(&odd);
        if len2 & 1 != 0 {
            crc1 = mat_times(&even, crc1);
        }
        len2 >>= 1;
        if len2 == 0 { break; }

        let next_odd = mat_square(&even);
        if len2 & 1 != 0 {
            crc1 = mat_times(&next_odd, crc1);
        }
        len2 >>= 1;
        if len2 == 0 { break; }

        odd = mat_square(&next_odd);
        // следующая итерация продолжает с новой odd
        // (упрощение: перепишем как явный цикл со swap)
    }
    crc1 ^ crc2
}

// ── CRC32 (таблица, совместимая с zlib) ──────────────────────────────

// Используем crc32fast — быстрее табличного и поддерживает SIMD
// (добавить в Cargo.toml: crc32fast = "1")
fn crc32_buf(data: &[u8]) -> u32 {
    crc32fast::hash(data)
}

// ── LFH serializer ───────────────────────────────────────────────────

fn write_lfh(buf: &mut Vec<u8>, idx: u32, crc: u32, comp_size: u64, uncomp_size: u64) {
    let fname = format!("{}.txt", idx);
    let fname_bytes = fname.as_bytes();
    let fname_len = fname_bytes.len() as u16;

    buf.extend_from_slice(&0x04034b50u32.to_le_bytes()); // signature
    buf.extend_from_slice(&20u16.to_le_bytes());         // version needed
    buf.extend_from_slice(&0u16.to_le_bytes());          // flags
    buf.extend_from_slice(&8u16.to_le_bytes());          // method: deflate
    buf.extend_from_slice(&0u16.to_le_bytes());          // mod time
    buf.extend_from_slice(&0u16.to_le_bytes());          // mod date
    buf.extend_from_slice(&crc.to_le_bytes());
    buf.extend_from_slice(&(comp_size as u32).to_le_bytes());
    buf.extend_from_slice(&(uncomp_size as u32).to_le_bytes());
    buf.extend_from_slice(&fname_len.to_le_bytes());
    buf.extend_from_slice(&0u16.to_le_bytes());          // extra len
    buf.extend_from_slice(fname_bytes);
}

// ── Основная функция, вызываемая из Python ───────────────────────────

#[pyfunction]
fn run_backward_pass(
    py: Python<'_>,
    num_files: u32,
    kernel_size: u64,
    kernel_crc32: u32,
    kernel_comp_size: u64,
) -> PyResult<(PyObject, PyObject, PyObject)> {

    let base_odd = build_base_odd();

    let n = (num_files + 1) as usize;
    let mut crcs:         Vec<u32> = vec![0u32; n];
    let mut comp_sizes:   Vec<u64> = vec![0u64; n];
    let mut uncomp_sizes: Vec<u64> = vec![0u64; n];

    let mut suffix_crc: u32 = kernel_crc32;
    let mut suffix_len: u64 = kernel_size;
    let mut cur_comp:   u64 = kernel_comp_size;
    let mut cur_uncomp: u64 = kernel_size;

    // Буфер для LFH — переиспользуем между итерациями
    let mut lfh_buf: Vec<u8> = Vec::with_capacity(64);

    for i in (1..=num_files).rev() {
        crcs[i as usize]         = suffix_crc;
        comp_sizes[i as usize]   = cur_comp;
        uncomp_sizes[i as usize] = cur_uncomp;

        // Строим LFH в переиспользуемом буфере
        lfh_buf.clear();
        write_lfh(&mut lfh_buf, i, suffix_crc, cur_comp, cur_uncomp);

        let lfh_len = lfh_buf.len() as u64;
        let lfh_crc = crc32_buf(&lfh_buf);

        suffix_crc  = crc32_combine(lfh_crc, suffix_crc, suffix_len, &base_odd);
        suffix_len += lfh_len;
        cur_comp   += 5 + lfh_len;   // 5 = quote header
        cur_uncomp += lfh_len;
    }

    // Преобразуем Vec<u32/u64> в bytes для Python
    // Безопасно: u32/u64 — Plain Old Data, выравнивание гарантировано
    let crcs_bytes = unsafe {
        std::slice::from_raw_parts(
            crcs.as_ptr() as *const u8,
            crcs.len() * 4,
        )
    };
    let comp_bytes = unsafe {
        std::slice::from_raw_parts(
            comp_sizes.as_ptr() as *const u8,
            comp_sizes.len() * 8,
        )
    };
    let uncomp_bytes = unsafe {
        std::slice::from_raw_parts(
            uncomp_sizes.as_ptr() as *const u8,
            uncomp_sizes.len() * 8,
        )
    };

    Ok((
        PyBytes::new(py, crcs_bytes).into(),
        PyBytes::new(py, comp_bytes).into(),
        PyBytes::new(py, uncomp_bytes).into(),
    ))
}

// ── Регистрация модуля ────────────────────────────────────────────────

#[pymodule]
fn backward(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(run_backward_pass, m)?)?;
    Ok(())
}