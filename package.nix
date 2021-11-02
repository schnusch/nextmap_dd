{ lib
, imagemagick
, python3Packages
}:

python3Packages.buildPythonApplication rec {
  pname = "nextmap_dd";
  version = "0.0.0";

  src = ./.;

  doCheck = false;

  propagatedBuildInputs = with python3Packages; [
    imagemagick
    selenium
  ];

  meta = with lib; {
    description = "Take a screenshot of Dresden's nextbike map.";
    homepage = "https://github.com/schnusch/nextmap_dd";
    license = licenses.agpl3;
  };
}
