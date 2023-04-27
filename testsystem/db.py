#
# Copyright 2023 EAS Group
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this 
# software and associated documentation files (the “Software”), to deal in the Software 
# without restriction, including without limitation the rights to use, copy, modify, 
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to 
# permit persons to whom the Software is furnished to do so, subject to the following 
# conditions:
#
# The above copyright notice and this permission notice shall be included in all copies 
# or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF 
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE 
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import testsystem.config as cnf
import sqlalchemy as sa
import sqlalchemy.orm as sao

from testsystem.config import get_config
from testsystem.constants import DB_CONN_TIMEOUT_S

engine = None
mapper_registry = sao.registry()
Base = mapper_registry.generate_base()


def init_database():
    global engine
    if engine is None:
        config = get_config()
        if config.db_type == "sqlite":
            # In memory db
            # engine = sa.create_engine(
            #    "sqlite+pysqlite:///:memory:", echo=False, future=True
            # )
            engine = sa.create_engine(
                f"sqlite+pysqlite:///{config.db_file}",
                echo=False,
                future=True,
                connect_args={"timeout": DB_CONN_TIMEOUT_S},
            )
        else:
            raise NotImplementedError(
                "Database type '{0}' is not supported.".format(config.db_type)
            )
        Base.metadata.create_all(engine)


def get_engine():
    """
    Returns the initialized database engine.
    """
    init_database()
    global engine
    return engine
