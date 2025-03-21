use pyo3::prelude::*;
use pyo3::types::PyModule;
use std::env;

fn main() -> PyResult<()> {
    pyo3::prepare_freethreaded_python();

    // Get the current executable's directory
    let mut current_dir = env::current_exe()?;

    println!("Current directory: {}", current_dir.display());

    // the generated code most of the time gen in <rust_root>/src/target/debug/rust_src
    for _i in 0..4u8 {
        current_dir.pop();
    }

    Python::with_gil(|py| {
        let sys = PyModule::import(py, "sys")?;
        sys.getattr("path")?
            .call_method1("append", (current_dir.to_string_lossy().to_string(),))?;

        let curses = PyModule::import(py, "curses")?;
        let interface = PyModule::import(py, "interface")?;
        let main_func = interface.getattr("main")?;
        let wrapper = curses.getattr("wrapper")?;
        wrapper.call1((main_func,))?;

        Ok(())
    })
}
