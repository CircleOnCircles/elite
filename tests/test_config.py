import textwrap

import pytest
from elite.config import Config, ConfigError


def test_config_inexistent(tmpdir):
    p = tmpdir.join('config.yaml')

    with pytest.raises(ConfigError):
        Config(p.strpath)


def test_config_invalid(tmpdir):
    p = tmpdir.join('config.yaml')
    p.write(textwrap.dedent('''\
        ---
        data1: - value1
        data2: 2
        data3: true
    '''))

    with pytest.raises(ConfigError):
        Config(p.strpath)


def test_config_wrong_data_type(tmpdir):
    p = tmpdir.join('config.yaml')
    p.write(textwrap.dedent('''\
        ---
        - data1
        - data2
        - data3
    '''))

    with pytest.raises(ConfigError):
        Config(p.strpath)


def test_config_basic(tmpdir):
    p = tmpdir.join('config.yaml')
    p.write(textwrap.dedent('''\
        ---
        data1: value1
        data2: 2
        data3: true
    '''))

    config = Config(p.strpath)
    assert config.data1 == 'value1'
    assert config.data2 == 2
    assert config.data3 is True


def test_config_tag_include_single(tmpdir):
    d = tmpdir.join('data.yaml')
    d.write(textwrap.dedent('''\
        ---
        reaction: wow
    '''))

    p = tmpdir.join('config.yaml')
    p.write(textwrap.dedent('''\
        ---
        name: booboohead
        data:
          !include data.yaml
    '''))

    config = Config(p.strpath)
    assert config.name == 'booboohead'
    assert config.data == {'reaction': 'wow'}


def test_config_tag_include_single_anchors_passed(tmpdir):
    d = tmpdir.join('data.yaml')
    d.write(textwrap.dedent('''\
        ---
        known_as: *name
    '''))

    p = tmpdir.join('config.yaml')
    p.write(textwrap.dedent('''\
        ---
        name: &name booboohead
        data:
          !include data.yaml
    '''))

    config = Config(p.strpath)
    assert config.name == 'booboohead'
    assert config.data == {'known_as': 'booboohead'}


def test_config_tag_include_multiple(tmpdir):
    d1 = tmpdir.join('data1.yaml')
    d1.write(textwrap.dedent('''\
        ---
        reaction: wow
    '''))

    d2 = tmpdir.join('data2.yaml')
    d2.write(textwrap.dedent('''\
        ---
        reaction: hmmm
    '''))

    p = tmpdir.join('config.yaml')
    p.write(textwrap.dedent('''\
        ---
        name: booboohead
        data:
          !include
          path: .
          extension: yaml
          files:
            - data1
            - data2
    '''))

    config = Config(p.strpath)
    assert config.name == 'booboohead'
    assert config.data == [
        {'reaction': 'wow'},
        {'reaction': 'hmmm'}
    ]


def test_config_tag_macos_font_invalid_number_of_arguments(tmpdir):
    p = tmpdir.join('config.yaml')
    p.write(textwrap.dedent('''\
        ---
        path: !macos_font [SourceCodePro-Regular, 16, yup]
    '''))

    with pytest.raises(ConfigError):
        Config(p.strpath)


def test_config_tag_join_path(tmpdir):
    p = tmpdir.join('config.yaml')
    p.write(textwrap.dedent('''\
        ---
        path: !join_path [/Users, fots, test.txt]
    '''))

    config = Config(p.strpath)
    assert config.path == '/Users/fots/test.txt'


def test_config_tag_first_existing_dir_exists(tmpdir):
    tmpdir.mkdir('dir2')
    tmpdir.mkdir('dir3')

    p = tmpdir.join('config.yaml')
    p.write(textwrap.dedent(f'''\
        ---
        path: !first_existing_dir
          - {tmpdir.strpath}/dir1
          - {tmpdir.strpath}/dir2
          - {tmpdir.strpath}/dir3
    '''))

    config = Config(p.strpath)
    assert config.path == f'{tmpdir.strpath}/dir2'


def test_config_tag_first_existing_dir_inexistent(tmpdir):
    p = tmpdir.join('config.yaml')
    p.write(textwrap.dedent(f'''\
        ---
        path: !first_existing_dir
          - {tmpdir.strpath}/dir1
          - {tmpdir.strpath}/dir2
          - {tmpdir.strpath}/dir3
    '''))

    config = Config(p.strpath)
    assert config.path is None
