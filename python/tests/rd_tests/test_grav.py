import datetime
from resdata import ResDataType
from resdata.resfile import ResdataKW, ResdataFile, openFortIO, FortIO
from resdata.grid import GridGenerator
from resdata.gravimetry import ResdataGrav
from resdata.util.test import TestAreaContext
from tests import ResdataTest


def write_kws(filename, kws):
    with openFortIO(filename + ".UNRST", mode=FortIO.WRITE_MODE) as f:
        seq_hdr = ResdataKW("SEQNUM", 1, ResDataType.RD_INT)
        seq_hdr[0] = 10

        header = ResdataKW("INTEHEAD", 67, ResDataType.RD_INT)
        header[64] = 1
        header[65] = 1
        header[66] = 2000

        seq_hdr.fwrite(f)
        header.fwrite(f)
        for kw in kws:
            kw.fwrite(f)

        seq_hdr[0] = 20
        header[66] = 2009

        seq_hdr.fwrite(f)
        header.fwrite(f)
        for kw in kws:
            kw.fwrite(f)

        seq_hdr[0] = 20
        header[66] = 2010

        seq_hdr.fwrite(f)
        header.fwrite(f)
        for kw in kws:
            kw.fwrite(f)

        header = ResdataKW("INTEHEAD", 95, ResDataType.RD_INT)
        header[14] = 1  # sets phase to oil
        header[94] = 100  # E100
        with openFortIO(filename + ".INIT", mode=FortIO.WRITE_MODE) as f:
            header.fwrite(f)
            for kw in kws:
                kw.fwrite(f)


class ResdataGravTest(ResdataTest):
    def setUp(self):
        self.grid = GridGenerator.create_rectangular((10, 10, 10), (1, 1, 1))

    def test_create(self):
        kws = [
            ResdataKW(kw, self.grid.getGlobalSize(), ResDataType.RD_FLOAT)
            for kw in [
                "PORO",
                "PORV",
                "PRESSURE",
                "SWAT",
                "OIL_DEN",
                "RPORV",
                "PORV_MOD",
                "FIPOIL",
                "RFIPOIL",
            ]
        ]
        int_kws = [
            ResdataKW(kw, self.grid.getGlobalSize(), ResDataType.RD_INT)
            for kw in ["FIP_NUM", "PVTNUM"]
        ]

        for kw in kws:
            for i in range(self.grid.getGlobalSize()):
                kw[i] = 0.5
        for kw in int_kws:
            for i in range(self.grid.getGlobalSize()):
                kw[i] = 0

        kws += int_kws

        with TestAreaContext("grav_init"):
            write_kws("TEST", kws)
            # The init file created here only contains a PORO field. More
            # properties must be added to this before it can be used for
            # any useful gravity calculations.
            init = ResdataFile("TEST.INIT")

            grav = ResdataGrav(self.grid, init)

            restart_file = ResdataFile("TEST.UNRST")
            restart_view = restart_file.restartView(sim_time=datetime.date(2000, 1, 1))

            grav.new_std_density(1, 0.5)
            grav.add_std_density(1, 0, 0.5)

            grav.add_survey_RPORV("rporv", restart_view)
            grav.add_survey_PORMOD("pormod", restart_view)
            grav.add_survey_FIP("fip", restart_view)
            grav.add_survey_RFIP("fip", restart_view)

            grav.eval("rporv", "pormod", (0, 0, 0), phase_mask=1)

            # Test that missing std_density raises
            grav = ResdataGrav(self.grid, init)
            with self.assertRaises(ValueError):
                grav.add_survey_FIP("fip", restart_view)

    def test_create_minimal(self):
        kws = [
            ResdataKW(kw, self.grid.getGlobalSize(), ResDataType.RD_FLOAT)
            for kw in [
                "PORO",
                "PORV",
                "SWAT",
                "OIL_DEN",
                "RPORV",
            ]
        ]

        with TestAreaContext("grav_init"):
            write_kws("TEST", kws)
            init = ResdataFile("TEST.INIT")

            grav = ResdataGrav(self.grid, init)

            restart_file = ResdataFile("TEST.UNRST")
            restart_view = restart_file.restartView(sim_time=datetime.date(2000, 1, 1))

            grav.new_std_density(1, 0.5)
            grav.add_std_density(1, 0, 0.5)

            grav.add_survey_RPORV("rporv", restart_view)
