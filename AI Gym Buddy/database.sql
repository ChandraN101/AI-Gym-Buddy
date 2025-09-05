
CREATE DATABASE mindcareai223;

USE mindcareai223;

-- Create the user table
CREATE TABLE user (
    id INT(11) NOT NULL AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    country VARCHAR(100) NOT NULL,
    PRIMARY KEY (id)
);

-- Create the profile table
CREATE TABLE profile (
    profile_id INT(11) NOT NULL AUTO_INCREMENT,
    user_id INT(11) NOT NULL,
    experience VARCHAR(50),
    weight FLOAT,
    height FLOAT,
    age INT(11),
    gender VARCHAR(10),
    injury VARCHAR(50),
    medication VARCHAR(10),
    bmi FLOAT,
    bmi_category Varchar(20),
    PRIMARY KEY (profile_id)
);
