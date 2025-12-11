import json
import logging
import multiprocessing as mp
import os

import dotenv
import json5
import typer

from runtime.multi_mode.config import load_mode_config

app = typer.Typer()


@app.command()
def modes(config_name: str) -> None:
    """
    Show information about available modes in a mode-aware configuration.

    Parameters
    ----------
    config_name : str
    """
    try:
        mode_config = load_mode_config(config_name)

        print("-" * 32)
        print(f"Mode System: {mode_config.name}")
        print(f"Default Mode: {mode_config.default_mode}")
        print(
            f"Manual Switching: {'Enabled' if mode_config.allow_manual_switching else 'Disabled'}"
        )
        print(
            f"Mode Memory: {'Enabled' if mode_config.mode_memory_enabled else 'Disabled'}"
        )

        if mode_config.global_lifecycle_hooks:
            print(f"Global Lifecycle Hooks: {len(mode_config.global_lifecycle_hooks)}")
        print()

        print("Available Modes:")
        print("-" * 50)
        for name, mode in mode_config.modes.items():
            is_default = " (DEFAULT)" if name == mode_config.default_mode else ""
            print(f"• {mode.display_name}{is_default}")
            print(f"  Name: {name}")
            print(f"  Description: {mode.description}")
            print(f"  Frequency: {mode.hertz} Hz")
            if mode.timeout_seconds:
                print(f"  Timeout: {mode.timeout_seconds} seconds")
            print(f"  Inputs: {len(mode._raw_inputs)}")
            print(f"  Actions: {len(mode._raw_actions)}")
            if mode.lifecycle_hooks:
                print(f"  Lifecycle Hooks: {len(mode.lifecycle_hooks)}")
            print()

        print("Transition Rules:")
        print("-" * 50)
        for rule in mode_config.transition_rules:
            from_display = (
                mode_config.modes[rule.from_mode].display_name
                if rule.from_mode != "*"
                else "Any Mode"
            )
            to_display = mode_config.modes[rule.to_mode].display_name
            print(f"• {from_display} → {to_display}")
            print(f"  Type: {rule.transition_type.value}")
            if rule.trigger_keywords:
                print(f"  Keywords: {', '.join(rule.trigger_keywords)}")
            print(f"  Priority: {rule.priority}")
            if rule.cooldown_seconds > 0:
                print(f"  Cooldown: {rule.cooldown_seconds}s")
            print()

    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_name}.json5")
        raise typer.Exit(1)
    except Exception as e:
        logging.error(f"Error loading mode configuration: {e}")
        raise typer.Exit(1)


@app.command()
def list_configs() -> None:
    """
    List all available configuration files.
    """
    config_dir = os.path.join(os.path.dirname(__file__), "../config")

    if not os.path.exists(config_dir):
        print("Configuration directory not found")
        return

    configs = []
    mode_configs = []

    for filename in os.listdir(config_dir):
        if filename.endswith(".json5"):
            config_name = filename[:-6]
            config_path = os.path.join(config_dir, filename)

            try:
                with open(config_path, "r") as f:
                    raw_config = json5.load(f)

                if "modes" in raw_config and "default_mode" in raw_config:
                    mode_configs.append(
                        (config_name, raw_config.get("name", config_name))
                    )
                else:
                    configs.append((config_name, raw_config.get("name", config_name)))
            except Exception as _:
                configs.append((config_name, "Invalid config"))

    print("-" * 32)
    if mode_configs:
        print("Mode-Aware Configurations:")
        print("-" * 32)
        for config_name, display_name in sorted(mode_configs):
            print(f"• {config_name} - {display_name}")
        print()

    print("-" * 32)
    if configs:
        print("Standard Configurations:")
        print("-" * 32)
        for config_name, display_name in sorted(configs):
            print(f"• {config_name} - {display_name}")


@app.command()
def validate_config(
    config_name: str = typer.Argument(
        ...,
        help="Configuration file name or path (e.g., 'test' or 'config/test.json5')",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed validation information"
    ),
    check_components: bool = typer.Option(
        False,
        "--check-components",
        help="Verify that all components (inputs, LLMs, actions) exist in codebase (slower but thorough)",
    ),
    skip_inputs: bool = typer.Option(
        False,
        "--skip-inputs",
        help="Skip input validation (useful for debugging)",
    ),
    allow_missing: bool = typer.Option(
        False,
        "--allow-missing",
        help="Allow missing components (only warn, don't fail)",
    ),
) -> None:
    """
    Validate an OM1 configuration file.

    Checks for:
    - Valid JSON5 syntax
    - Schema compliance (required fields, correct types)
    - API key configuration (warning only)
    - Component existence (with --check-components flag)

    Examples:
        uv run src/cli.py validate-config test
        uv run src/cli.py validate-config config/my_robot.json5
        uv run src/cli.py validate-config test --verbose
        uv run src/cli.py validate-config test --check-components
        uv run src/cli.py validate-config test --check-components --skip-inputs
        uv run src/cli.py validate-config test --check-components --allow-missing
    """
    try:
        # 1. Resolve config path
        config_path = _resolve_config_path(config_name)

        if verbose:
            print(f"📁 Validating: {config_path}")
            print("-" * 50)

        # 2. Load and parse JSON5
        with open(config_path, "r") as f:
            raw_config = json5.load(f)

        if verbose:
            print("✅ JSON5 syntax valid")

        # 3. Detect config type
        is_multi_mode = "modes" in raw_config and "default_mode" in raw_config
        config_type = "multi-mode" if is_multi_mode else "single-mode"

        if verbose:
            print(f"✅ Detected {config_type} configuration")

        # 4. Schema validation
        schema_file = (
            "multi_mode_schema.json" if is_multi_mode else "single_mode_schema.json"
        )
        schema_path = os.path.join(
            os.path.dirname(__file__), "../config/schema", schema_file
        )

        with open(schema_path, "r") as f:
            schema = json.load(f)

        from jsonschema import validate

        validate(instance=raw_config, schema=schema)

        if verbose:
            print("✅ Schema validation passed")

        # 5. Component validation (if requested)
        if check_components:
            if not verbose:
                print(
                    "⏳ Validating components (this may take a moment)...",
                    end="",
                    flush=True,
                )
            _validate_components(
                raw_config, is_multi_mode, verbose, skip_inputs, allow_missing
            )
            if not verbose:
                print("\r✅ All components validated successfully!           ")

        # 6. API key check (warning only)
        _check_api_key(raw_config, verbose)

        # 7. Success message
        print()
        print("=" * 50)
        print("✅ Configuration is valid!")
        print("=" * 50)

        if verbose:
            _print_config_summary(raw_config, is_multi_mode)

    except FileNotFoundError as e:
        print("❌ Error: Configuration file not found")
        print(f"   {e}")
        raise typer.Exit(1)

    # Fix: Handle JSON5 parsing errors without using json5.JSON5Error
    except ValueError as e:
        # Check if it's a JSON5 parsing error by looking for line/column info
        if (
            "line" in str(e).lower()
            or "col" in str(e).lower()
            or "parse" in str(e).lower()
        ):
            print("❌ Error: Invalid JSON5 syntax")
            print(f"   {e}")
            raise typer.Exit(1)
        # Re-raise if it's a validation error we've already handled
        elif "Component validation" in str(e):
            raise typer.Exit(1)
        # Otherwise, treat as unexpected error
        else:
            print("❌ Error: Unexpected validation error")
            print(f"   {e}")
            if verbose:
                import traceback

                traceback.print_exc()
            raise typer.Exit(1)

    # Handle component validation errors specifically
    except Exception as e:
        if "Component validation" in str(e):
            raise typer.Exit(1)
        else:
            print("❌ Error: Unexpected validation error")
            print(f"   {e}")
            if verbose:
                import traceback

                traceback.print_exc()
            raise typer.Exit(1)


def _resolve_config_path(config_name: str) -> str:
    """
    Resolve configuration path from name or path.

    Parameters
    ----------
    config_name : str
        Configuration name or path

    Returns
    -------
    str
        Absolute path to configuration file

    Raises
    ------
    FileNotFoundError
        If configuration file cannot be found
    """
    # If it's already a path that exists
    if os.path.exists(config_name):
        return os.path.abspath(config_name)

    # Try with .json5 extension
    if os.path.exists(config_name + ".json5"):
        return os.path.abspath(config_name + ".json5")

    # Try in config directory
    config_dir = os.path.join(os.path.dirname(__file__), "../config")
    config_path = os.path.join(config_dir, config_name)

    if os.path.exists(config_path):
        return os.path.abspath(config_path)

    if os.path.exists(config_path + ".json5"):
        return os.path.abspath(config_path + ".json5")

    raise FileNotFoundError(
        f"Configuration '{config_name}' not found. "
        f"Tried: {config_name}, {config_name}.json5, {config_path}, {config_path}.json5"
    )


def _validate_components(
    raw_config: dict,
    is_multi_mode: bool,
    verbose: bool,
    skip_inputs: bool = False,
    allow_missing: bool = False,
):
    """
    Validate that all component types exist in codebase.
    """
    errors = []
    warnings = []

    if verbose:
        print("🔍 Checking component existence...")

    try:
        # SIMPLIFIED APPROACH: Direct validation without complex collection
        if is_multi_mode:
            # Validate global LLM if present
            if "cortex_llm" in raw_config:
                llm_type = raw_config["cortex_llm"].get("type")
                if llm_type and verbose:
                    print(f"  Checking global LLM: {llm_type}")
                if llm_type and not _check_llm_exists(llm_type):
                    if allow_missing:
                        warnings.append(f"Global LLM type '{llm_type}' not found")
                    else:
                        errors.append(f"Global LLM type '{llm_type}' not found")

            # Validate each mode
            for mode_name, mode_data in raw_config.get("modes", {}).items():
                if verbose:
                    print(f"  Validating mode: {mode_name}")
                mode_errors, mode_warnings = _validate_mode_components(
                    mode_name, mode_data, verbose, skip_inputs, allow_missing
                )
                errors.extend(mode_errors)
                warnings.extend(mode_warnings)
        else:
            # Single mode validation
            if verbose:
                print("  Validating single-mode configuration")
            mode_errors, mode_warnings = _validate_mode_components(
                "config", raw_config, verbose, skip_inputs, allow_missing
            )
            errors.extend(mode_errors)
            warnings.extend(mode_warnings)

    except Exception as e:
        error_msg = f"Component validation error: {e}"
        if allow_missing:
            warnings.append(error_msg)
        else:
            errors.append(error_msg)
        if verbose:
            import traceback

            traceback.print_exc()

    # Print warnings if any
    if warnings:
        print("⚠️  Component validation warnings:")
        for warning in warnings:
            print(f"   - {warning}")

    # Print errors if any
    if errors:
        print("❌ Component validation failed:")
        for error in errors:
            print(f"   - {error}")
        raise Exception("Component validation failed")

    if verbose:
        print("✅ All components exist")


def _validate_mode_components(
    mode_name: str,
    mode_data: dict,
    verbose: bool,
    skip_inputs: bool = False,
    allow_missing: bool = False,
) -> tuple:
    """
    Validate components for a single mode.
    Returns (errors, warnings) tuple.
    """
    errors = []
    warnings = []

    try:
        # Check inputs (unless skipped)
        if not skip_inputs:
            inputs = mode_data.get("agent_inputs", [])
            if verbose and inputs:
                print(f"    Checking {len(inputs)} inputs...")

            for inp in inputs:
                input_type = inp.get("type")
                if input_type:
                    if verbose:
                        print(f"      Input: {input_type}", end=" ")
                    if not _check_input_exists(input_type):
                        msg = f"[{mode_name}] Input type '{input_type}' not found"
                        if allow_missing:
                            warnings.append(msg)
                            if verbose:
                                print("⚠️")
                        else:
                            errors.append(msg)
                            if verbose:
                                print("❌")
                    else:
                        if verbose:
                            print("✅")
        else:
            if verbose:
                print("    ⏭️  Skipping input validation")

        # Check LLM
        if "cortex_llm" in mode_data:
            llm_type = mode_data["cortex_llm"].get("type")
            if llm_type:
                if verbose:
                    print(f"    LLM: {llm_type}", end=" ")
                if not _check_llm_exists(llm_type):
                    msg = f"[{mode_name}] LLM type '{llm_type}' not found"
                    if allow_missing:
                        warnings.append(msg)
                        if verbose:
                            print("⚠️")
                    else:
                        errors.append(msg)
                        if verbose:
                            print("❌")
                else:
                    if verbose:
                        print("✅")

        # Check simulators
        simulators = mode_data.get("simulators", [])
        if verbose and simulators:
            print(f"    Checking {len(simulators)} simulators...")

        for sim in simulators:
            sim_type = sim.get("type")
            if sim_type:
                if verbose:
                    print(f"      Simulator: {sim_type}", end=" ")
                if not _check_simulator_exists(sim_type):
                    msg = f"[{mode_name}] Simulator type '{sim_type}' not found"
                    if allow_missing:
                        warnings.append(msg)
                        if verbose:
                            print("⚠️")
                    else:
                        errors.append(msg)
                        if verbose:
                            print("❌")
                else:
                    if verbose:
                        print("✅")

        # Check actions
        actions = mode_data.get("agent_actions", [])
        if verbose and actions:
            print(f"    Checking {len(actions)} actions...")

        for action in actions:
            action_name = action.get("name")
            connector = action.get("connector")
            if action_name:
                if verbose:
                    print(
                        f"      Action: {action_name} (connector: {connector})", end=" "
                    )
                if not _check_action_exists(action_name, connector):
                    msg = f"[{mode_name}] Action '{action_name}' with connector '{connector}' not found"
                    if allow_missing:
                        warnings.append(msg)
                        if verbose:
                            print("⚠️")
                    else:
                        errors.append(msg)
                        if verbose:
                            print("❌")
                else:
                    if verbose:
                        print("✅")

        # Check backgrounds
        backgrounds = mode_data.get("backgrounds", [])
        if verbose and backgrounds:
            print(f"    Checking {len(backgrounds)} backgrounds...")

        for bg in backgrounds:
            bg_type = bg.get("type")
            if bg_type:
                if verbose:
                    print(f"      Background: {bg_type}", end=" ")
                if not _check_background_exists(bg_type):
                    msg = f"[{mode_name}] Background type '{bg_type}' not found"
                    if allow_missing:
                        warnings.append(msg)
                        if verbose:
                            print("⚠️")
                    else:
                        errors.append(msg)
                        if verbose:
                            print("❌")
                else:
                    if verbose:
                        print("✅")

    except Exception as e:
        msg = f"[{mode_name}] Error during validation: {e}"
        if allow_missing:
            warnings.append(msg)
        else:
            errors.append(msg)
        if verbose:
            print(f"    Error: {e}")

    return errors, warnings


def _check_input_exists(input_type: str) -> bool:
    """Check if input type exists."""
    try:
        # METHOD 1: Try simple module existence check first (no imports)
        try:
            import importlib

            importlib.import_module(f"inputs.{input_type}")
            return True
        except ImportError:
            return False
        except Exception:
            return False

    except Exception:
        return False


def _check_llm_exists(llm_type: str) -> bool:
    """Check if LLM type exists."""
    try:
        # METHOD 1: Try simple module existence check first (no imports)
        try:
            import importlib

            importlib.import_module(f"llm.{llm_type}")
            return True
        except ImportError:
            return False
        except Exception:
            return False

    except Exception:
        return False


def _check_simulator_exists(sim_type: str) -> bool:
    """Check if simulator type exists."""
    try:
        # METHOD 1: Try simple module existence check first (no imports)
        try:
            import importlib

            importlib.import_module(f"simulators.{sim_type}")
            return True
        except ImportError:
            return False
        except Exception:
            return False

    except Exception:
        return False


def _check_action_exists(action_name: str, connector: str) -> bool:
    """Check if action exists."""
    try:
        import importlib

        # METHOD 1: Try simple module existence check first (no imports)
        try:
            importlib.import_module(f"actions.{action_name}.interface")
            return True
        except ImportError:
            return False
        except Exception:
            return False

    except Exception:
        return False


def _check_background_exists(bg_type: str) -> bool:
    """Check if background type exists."""
    try:
        # METHOD 1: Try simple module existence check first (no imports)
        try:
            import importlib

            importlib.import_module(f"backgrounds.{bg_type}")
            return True
        except ImportError:
            return False
        except Exception:
            return False

    except Exception:
        return False


def _check_api_key(raw_config: dict, verbose: bool):
    """Check API key configuration (warning only)."""
    api_key = raw_config.get("api_key", "")

    if not api_key or api_key == "openmind_free" or api_key == "":
        print()
        print("⚠️  Warning: No API key configured")
        print("   Get a free key at: https://portal.openmind.org")
        print("   Or set OM_API_KEY in your .env file")
    elif verbose:
        print("✅ API key configured")


def _print_config_summary(raw_config: dict, is_multi_mode: bool):
    """Print configuration summary."""
    print()
    print("📋 Configuration Summary:")
    print("-" * 50)

    if is_multi_mode:
        print("   Type: Multi-mode")
        print(f"   Name: {raw_config.get('name', 'N/A')}")
        print(f"   Default Mode: {raw_config.get('default_mode')}")
        print(f"   Modes: {len(raw_config.get('modes', {}))}")
        print(f"   Transition Rules: {len(raw_config.get('transition_rules', []))}")
    else:
        print("   Type: Single-mode")
        print(f"   Name: {raw_config.get('name', 'N/A')}")
        print(f"   Frequency: {raw_config.get('hertz', 'N/A')} Hz")
        print(f"   Inputs: {len(raw_config.get('agent_inputs', []))}")
        print(f"   Actions: {len(raw_config.get('agent_actions', []))}")


if __name__ == "__main__":

    # Fix for Linux multiprocessing
    if mp.get_start_method(allow_none=True) != "spawn":
        mp.set_start_method("spawn")

    dotenv.load_dotenv()
    app()
